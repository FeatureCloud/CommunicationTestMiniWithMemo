from FeatureCloud.app.engine.app import AppState, app_state

# FeatureCloud requires that apps define the at least the 'initial' state.
# This state is executed after the app instance is started.
P2PDATA = 2
BROADCASTDATA = 3
STARMEMOAGG = 5
STARMEMOGATHER = 7
STARMEMOAWAIT = 11
STARMEMOAWAITSMPC = 13
STARMEMOAWAITDP = 17
STARMEMOAWAITSMPCDP = 19
@app_state('initial')
class InitialState(AppState):

    def register(self):
        self.register_transition('waity')  
        self.register_transition("letssee")
        # We declare that 'terminal' state is accessible from the 'initial' state.

    def run(self):
        # Order of send and await is reversed to check that memos do what they
        # should do
        self.send_data_to_coordinator(STARMEMOAWAITSMPCDP, use_smpc = True, use_dp = True, memo="STARMEMOAWAITSMPCDP")
        self.send_data_to_coordinator(STARMEMOAWAITDP, use_dp = True, memo="STARMEMOAWAITDP")
        self.send_data_to_coordinator(STARMEMOAWAITSMPC, use_smpc= True, memo="STARMEMOAWAITSMPC")
        self.send_data_to_coordinator(STARMEMOAWAIT, memo="STARMEMOAWAIT")
        self.send_data_to_coordinator(STARMEMOGATHER, memo="STARMEMOGATHER")
        self.send_data_to_coordinator(STARMEMOAGG, memo="STARMEMOAGG")
        if self.id == sorted(self.clients)[1]:
            print("I am the sender for the p2p Test")
            self.send_data_to_participant(P2PDATA, sorted(self.clients)[0], memo="P2PDATA")
        elif self.id == sorted(self.clients)[0]:
            print("I am the receiver for the p2p Test")
        
        
        if self.is_coordinator:
            return "letssee"
        else:
            return "waity"  
        # This means we are done. If the coordinator transitions into the 
        # 'terminal' state, the whole computation will be shut down.

@app_state('letssee')
class AggState(AppState):
    def register(self):
        self.register_transition("terminal")
    def run(self):
        #p2p
        if self.id == sorted(self.clients)[0]:
            p2pdata = self.await_data(n=1, is_json=False, memo="P2PDATA")
            print("test p2p: ", end="")
            if p2pdata == P2PDATA:
                print(f"passed ({p2pdata})")
            else:
                print(f"failed ({p2pdata})")
    
        # agg
        aggdata = self.aggregate_data(memo="STARMEMOAGG")
        print("test agg: ", end="")
        if aggdata == sum([STARMEMOAGG for _ in range(len(self.clients))]):
            print(f"passed ({aggdata})")
        else:
            print(f"failed ({aggdata})")
        # gather
        gatherdata = self.gather_data(memo="STARMEMOGATHER")
        print("test gather: ", end="")
        if gatherdata == [STARMEMOGATHER for _ in range(len(self.clients))]:
            print(f"passed ({gatherdata})")
        else:
            print(f"failed ({gatherdata})")
        # await
        awaitdata = self.await_data(n=len(self.clients), is_json=False, memo="STARMEMOAWAIT")
        print("test await: ", end="")
        if awaitdata == [STARMEMOAWAIT for _ in range(len(self.clients))]:
            print(f"passed ({awaitdata})")
        else:
            print(f"failed ({awaitdata})")
        # await smpc
        awaitdatasmpc = self.await_data(use_smpc=True, memo="STARMEMOAWAITSMPC")
        print("test awaitSMPC: ", end="")
        if awaitdatasmpc == sum([STARMEMOAWAITSMPC for _ in range(len(self.clients))]):
            print(f"passed ({awaitdatasmpc})")
        else:
            print(f"failed ({awaitdatasmpc})")
        # await dp
        awaitdatadp = self.await_data(n=len(self.clients), use_dp=True, memo="STARMEMOAWAITDP")
        print("test awaitDP: ", end="")
        print(f"got ({awaitdatadp}), expected noised ({STARMEMOAWAITDP})")
        # await dp + smpc
        awaitsmpcdp = self.await_data(use_smpc=True, use_dp=True, memo="STARMEMOAWAITSMPCDP")
        print("test awaitSMPCDP: ", end="")
        print(f"got ({awaitsmpcdp}), expected noised and aggregated ({STARMEMOAWAITSMPCDP})")
        # broadcast data
        self.broadcast_data(BROADCASTDATA, send_to_self=False, memo="BROADCASTDATA")

        return "terminal"

@app_state("waity")
class getBroadcastShitState(AppState):
    def register(self):
        self.register_transition("terminal")
    def run(self):
        #p2p
        # if self.id == sorted(self.clients)[0]:
        #     p2pdata = self.await_data(n=1, is_json=False, memo="P2PDATA")
        #     print("test p2p: ", end="")
        #     if p2pdata == P2PDATA:
        #         print(f"passed ({p2pdata})")
        #     else:
        #         print(f"failed ({p2pdata})")
        # get broadcasted stuff
        broadcastdata = self.await_data(n=1, memo="BROADCASTDATA")
        print("test broadcast: ", end="")
        if broadcastdata == BROADCASTDATA:
            print(f"passed ({broadcastdata})")
        else:
            print(f"failed ({broadcastdata}")
        return "terminal"
