from FeatureCloud.app.engine.app import AppState, app_state, _aggregate, SMPCOperation
import random
import numpy as np
import json
from copy import deepcopy

# This app does a random order of random communication methods in featurecloud
# and tests if the communication method worked
# The tests are generated randomly with the following variables:
# DATATYPES = ["string", 1, 1.0, {'key1': 'value1', 'key2': 'value2'}, [1,2,3.0]] 
# COM_METHODS = ["p2p", "gather"]
# SEND_METHOD = ["broadcast", "send_to_coord"] 
# AGG_METHOD = ["aggregate", "await", "gather"] 
# SMPC = True/False
# DP = True/False
# memo = None/generated
# the send method describes whether the send_data_to_participant (p2p) method 
# or the send_data_to_coordinator or broiadcast (gather) method is used

### VARIABLES
NUM_EXPERIMENTS = 100
TEST_SMPC_WEIGHTS = [0.5, 0.5] # weights with which to choose from [TRUE, FALSE]
TEST_DP_WEIGHTS = [0.5, 0.5] # weights with which to choose from [TRUE, FALSE]
DEBUG = False

### CONSTANTS
DATATYPES = ["string", 2, 1.5, {'key1': 'value1', 'key2': 'value2'}, [1,2,3.0], np.array([1,2,3]), {"val1": 1, "val2": 5.0, "val3": [1, 3.7], "val4": np.array([1,2.1,3])}] 
NON_SMPC_DATA = [0, 3] # indexes of data in DATATYPES which does not work with SMPC (e.g. strings)
NON_DP_DATA = [0, 3] # indexes of data in DATATYPES which does not work with DP (e.g. strings)
NON_AGGREGATE_DATA = [0, 3, 6] # indexes of data in DATATYPES which does not work with aggregate (e.g. strings)
DATATYPES_WEIGHTS = [0.17, 0.17, 0.17, 0.17, 0.17, 0.17, 0.17] 
#DATATYPES = [1] 
    # CAREFUL CHANGING DATATYPES, it is expected that only index 0 and 3 contain
    # strings, as strings are incompatable with aggregate and smpc
COM_METHODS = ["p2p", "gather"] # Specify to only test peer to peer or gather schemes
COM_METHODS_WEIGHTS = [0.3, 0.7] # the weight with which to choose randomly
                                 # from COM_METHODS
SEND_METHOD = ["broadcast", "send_to_coord"] # specify the sending mode to test
SEND_METHOD_WEIGHTS = [0.5, 0.5]  # the weight with which to choose randomly
                                  # from COM_METHODS
AGG_METHOD = ["aggregate", "await", "gather"] # specify the gathering function to test
AGG_METHOD_WEIGHTS = [0.33, 0.33, 0.34] # the weight with which to choose randomly
                                        # from AGG_METHOD
#AGG_METHOD = ["aggregate"] 
SMPC_OPERATION = [SMPCOperation.ADD, SMPCOperation.MULTIPLY]
SMPC_OPERATION_WEIGHTS = [0.5, 0.5] # the weight with which to choose randomly
                                    # from SMPC_OPERATION


@app_state('initial')
class InitialState(AppState):

    def register(self):
        self.register_transition('terminal')  
        # We declare that 'terminal' state is accessible from the 'initial' state.

    def run(self):
        print(self.clients)
        # coord defines experiments and sends them around
        if self.is_coordinator:
            experiments = []
            for expNumber in range(NUM_EXPERIMENTS):
                # define all relevant variables
                comMethod = random.sample(COM_METHODS, k = 1)[0]
                useMemo = random.choice([True, False])
                memo = None
                smpc = False
                dp = False
                sendMethod = random.choices(population=SEND_METHOD, weights=SEND_METHOD_WEIGHTS, k=1)[0]
                aggMethod = random.choices(population=AGG_METHOD, weights=AGG_METHOD_WEIGHTS, k=1)[0]
                smpcOperation = random.choices(population=SMPC_OPERATION, weights= SMPC_OPERATION_WEIGHTS, k=1)[0]
                
                # ensure that they are set correctly
                #dp
                dp = random.choices(population=[True, False], weights=TEST_DP_WEIGHTS ,k=1)[0]

                #smpc
                if sendMethod != "broadcast":
                    smpc = random.choices(population=[True, False], weights=TEST_SMPC_WEIGHTS, k=1)[0]

                # filter which datatypes are possible and select from those
                specificRemoveIdxs = set()
                if comMethod == "gather" and aggMethod == "aggregate":
                    for idx in NON_AGGREGATE_DATA:
                        specificRemoveIdxs.add(idx)
                if comMethod == "gather" and smpc:
                    for idx in NON_SMPC_DATA:
                        specificRemoveIdxs.add(idx)
                if dp:
                    for idx in NON_DP_DATA:
                        specificRemoveIdxs.add(idx)
                data = random.choices(population=[val for idx, val in enumerate(DATATYPES) if idx not in specificRemoveIdxs],
                                      weights=[val for idx, val in enumerate(DATATYPES_WEIGHTS) if idx not in specificRemoveIdxs],
                                      k=1)[0]

                if useMemo or comMethod == "p2p":
                    memo = f"EXPERIMENT_NUMBER_{expNumber}"
                if comMethod == "p2p":
                    sender, receiver = tuple(random.sample(self.clients, k=2))
                    experiments.append({"com_method": "p2p", 
                                        "data": data,
                                        "sender": sender,
                                        "receiver": receiver,
                                        "dp": dp,
                                        "memo": memo})
                elif comMethod == "gather":
                    experiments.append({"com_method": "gather",
                                        "data": data,
                                        "send_method": sendMethod,
                                        "agg_method": aggMethod,
                                        "smpc": smpc,
                                        "smpc_operation": smpcOperation,
                                        "dp": dp,
                                        "memo": memo})
                else:
                    print(f"comMethod {comMethod} not implemented")
                    raise NotImplementedError
                
            # now send the experiments around
            self.broadcast_data(experiments, send_to_self=False, 
                                use_dp = False, 
                                memo = "initialExperimentExchange")
            ### DO EXPERIMENTS COORDINATOR
            print("EXPERIMENTS:")
            for x in experiments:
                print(x)
            for setup in experiments:
                # p2p
                if setup["com_method"] == "p2p":
                    if setup["sender"] == self.id:
                        if DEBUG:
                            print(f"SENDING P2P: {setup}")
                        if setup["memo"]:
                            self.send_data_to_participant(setup["data"], 
                                destination = setup["receiver"],
                                use_dp = setup["dp"],
                                memo = setup["memo"])
                        else:
                            self.send_data_to_participant(setup["data"], 
                                destination = setup["receiver"],
                                use_dp = setup["dp"])
                    if setup["receiver"] == self.id:
                        if DEBUG:
                            print(f"RECEVING P2P: {setup}")
                        if setup["memo"]:
                            receivedData = self.await_data(n=1, 
                                                      use_dp = setup["dp"],
                                                      memo = setup["memo"])
                        else:
                            receivedData = self.await_data(n=1, 
                                                      use_dp = setup["dp"])
                        if setup["dp"]:
                            print(f"TEST RESULT UNKNOWN (DP){setup}: GOT {receivedData}, should get {setup['data']}")
                        else:
                            if compare_objects(receivedData, setup["data"]):
                                print(f"TEST PASSED: {setup}")
                            else:
                                print(f"TEST FAILED: {setup} GOT DATA: {receivedData}, should get {setup['data']}")
                # gather (all except p2p)
                elif setup["com_method"] == "gather":
                    # gather as coordinator
                    if setup["send_method"] == "broadcast":
                        # send out data
                        if DEBUG:
                            print(f"SENDING BROADCAST: {setup}")
                        if setup["memo"]:
                            self.broadcast_data(setup["data"], 
                                            send_to_self=True, 
                                            use_dp = setup["dp"], 
                                            memo = setup["memo"])
                        else:
                            self.broadcast_data(setup["data"], 
                                            send_to_self=True, 
                                            use_dp = setup["dp"])
                    elif setup["send_method"] == "send_to_coord":
                        # first send, then use agg_method
                        if DEBUG:
                            print(f"SENDING GATHER: {setup}")
                        if setup["smpc"]:
                            self.configure_smpc(operation = setup["smpc_operation"])
                        if setup["memo"]:
                            self.send_data_to_coordinator(setup["data"],
                                                    send_to_self=True, 
                                                    use_smpc=setup["smpc"],
                                                    use_dp=setup["dp"],
                                                    memo=setup["memo"])
                        else:
                            self.send_data_to_coordinator(setup["data"],
                                                    send_to_self=True, 
                                                    use_smpc=setup["smpc"],
                                                    use_dp=setup["dp"])
                            
                        # now use the aggregation method
                        actualData = None
                        shouldData = None
                        if setup["agg_method"] == "aggregate":
                            if DEBUG:
                                print(f"RECEVING AGGREGATE: {setup}")
                            if setup["memo"]:
                                actualData = self.aggregate_data(
                                                use_smpc=setup["smpc"],
                                                use_dp=setup["dp"],
                                                memo=setup["memo"])
                            else:
                                actualData = self.aggregate_data(
                                                use_smpc=setup["smpc"],
                                                use_dp=setup["dp"])

                        elif setup["agg_method"] == "await":
                            if DEBUG:
                                print(f"RECEVING AWAIT: {setup}")
                            if setup["memo"]:
                                actualData = self.await_data(n=len(self.clients),
                                                use_smpc=setup["smpc"],
                                                use_dp=setup["dp"],
                                                memo=setup["memo"])
                            else:
                                actualData = self.await_data(n=len(self.clients),
                                                use_smpc=setup["smpc"],
                                                use_dp=setup["dp"])

                        elif setup["agg_method"] == "gather":
                            if DEBUG:
                                print(f"RECEVING GATHER: {setup}")
                            if setup["memo"]:
                                actualData = self.gather_data(
                                                use_smpc=setup["smpc"],
                                                use_dp=setup["dp"],
                                                memo=setup["memo"])
                            else:
                                actualData = self.gather_data(
                                                use_smpc=setup["smpc"],
                                                use_dp=setup["dp"])
                        else:
                            print("comMethod not implemented")
                            raise NotImplementedError
                        # evaluate the test
                        if setup["dp"]:
                            print(f"TEST RESULT UNKNOWN (DP){setup}: GOT {actualData}, should get {setup['data']}")
                        elif setup["smpc"] or setup["agg_method"] == "aggregate":
                            try:
                                shouldData = _aggregate([setup["data"] for _ in range(len(self.clients))], setup["smpc_operation"])
                            except:
                                shouldData = None
                                print(f"TEST RESULTS UNKNOWN (CANT AGGREGATE): {setup}, GOT {actualData}, WANT {setup['data']}")
                            if setup["agg_method"] == "gather":
                                actualData = actualData[0] # unwrap the data
                            if setup["smpc_operation"].value == SMPCOperation.MULTIPLY.value:
                                print(f"TEST RESULTS UNKNOWN (Multiply SMPC produces noise): {setup}, GOT {actualData}, WANT {setup['data']}")
                            else:
                                if compare_objects(shouldData, actualData):
                                    print(f"TEST PASSED: {setup}")
                                else:
                                    print(f"TEST FAILED: {setup} GOT DATA: {actualData}, should get {shouldData}")
                        else:
                            # gather or await     
                            shouldData = [setup["data"] for _ in range(len(self.clients))]         
                            if compare_objects(actualData, shouldData):
                                print(f"TEST PASSED: {setup}")
                            else:
                                print(f"TEST FAILED: {setup} GOT DATA: {actualData}, should get {shouldData}")
                else:
                    print("comMethod not implemented")
                    raise NotImplementedError
        else:
            ### DO EXPERIMENTS CLIENT
            # first get the experiments
            experiments = self.await_data(n=1, 
                                          memo = "initialExperimentExchange")
            print("EXPERIMENTS:")
            for x in experiments:
                print(x)
            for setup in experiments:
                # p2p
                if setup["com_method"] == "p2p":
                    if setup["sender"] == self.id:
                        if DEBUG:
                            print(f"SENDING P2P: {setup}")
                        if setup["memo"]:
                            self.send_data_to_participant(setup["data"], 
                                destination = setup["receiver"],
                                use_dp = setup["dp"],
                                memo = setup["memo"])
                        else:
                            self.send_data_to_participant(setup["data"], 
                                destination = setup["receiver"],
                                use_dp = setup["dp"])
                    if setup["receiver"] == self.id:
                        if DEBUG:
                            print(f"RECEIVING P2P: {setup}")
                        if setup["memo"]:
                            receivedData = self.await_data(n=1, 
                                                      use_dp = setup["dp"],
                                                      memo = setup["memo"])
                        else:
                            receivedData = self.await_data(n=1, 
                                                      use_dp = setup["dp"])
                        if setup["dp"]:
                                print(f"TEST RESULT UNKNOWN (DP){setup}: GOT {receivedData}, should get {setup['data']}")
                        else:
                            if compare_objects(receivedData, setup["data"]):
                                print(f"TEST PASSED: {setup}")
                            else:
                                print(f"TEST FAILED: {setup} GOT DATA: {receivedData}, should get {setup['data']}")
                
                # gather (all except p2p)
                elif setup["com_method"] == "gather":
                    # gather as client
                    if setup["send_method"] == "broadcast":
                        if DEBUG:
                            print(f"RECEIVING BROADCAST: {setup}")
                        # send out data
                        if setup["memo"]:
                            broadcastData = self.await_data(n=1, 
                                                use_dp = setup["dp"], 
                                                memo = setup["memo"])
                        else:
                            broadcastData = self.await_data(n=1, 
                                                use_dp = setup["dp"])
                        if setup["dp"]:
                            print(f"TEST RESULT UNKNOWN (DP){setup}: GOT {broadcastData}, should get {setup['data']}")
                        else:
                            if compare_objects(broadcastData, setup["data"]):
                                print(f"TEST PASSED: {setup}")
                            else:
                                print(f"TEST FAILED: {setup} GOT DATA: {broadcastData}, should get {setup['data']}")

                    elif setup["send_method"] == "send_to_coord":
                        # just send, aggregation and test done by coordinator
                        if DEBUG:
                            print(f"SENDING GATHER: {setup}")
                        if setup["smpc"]:
                            self.configure_smpc(operation = setup["smpc_operation"])
                        if setup["memo"]:
                            self.send_data_to_coordinator(setup["data"],
                                                    use_smpc=setup["smpc"],
                                                    use_dp=setup["dp"],
                                                    memo=setup["memo"])
                        else:
                            self.send_data_to_coordinator(setup["data"],
                                                    use_smpc=setup["smpc"],
                                                    use_dp=setup["dp"])
                            
                else:
                    print("comMethod not implemented")
                    raise NotImplementedError
        
        return "terminal"

def compare_objects(obj1, obj2):
    if isinstance(obj1, (int, float, np.int64)) and isinstance(obj2, (int, float, np.int64)):
        return float(obj1) == float(obj2)
    elif isinstance(obj1, (np.ndarray, list)) and isinstance(obj2, (np.ndarray, list)):
        for x,y in zip(obj1, obj2):
            if not compare_objects(x,y):
                return False
            else: 
                return True
    elif type(obj1) != type(obj2):
        print(f"FAILING: got types: {type(obj1)} and {type(obj2)}")
        return False
    elif isinstance(obj1, (int, float, str)):
        return obj1 == obj2
    elif isinstance(obj1, dict):
        return json.dumps(obj1, sort_keys=True, cls=_NumpyArrayEncoder) == json.dumps(obj2, sort_keys=True, cls=_NumpyArrayEncoder)
    elif isinstance(obj1, np.ndarray):
        return np.array_equal(obj1, obj2)
    elif isinstance(obj1, list):
        for x,y in zip(obj1, obj2):
            if not compare_objects(x,y):
                return False
            else: 
                return True
    else:
        return obj1 == obj2
    
class _NumpyArrayEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            # call default Encoder in other cases
            return json.JSONEncoder.default(self, obj)