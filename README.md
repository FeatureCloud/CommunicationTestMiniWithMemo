# Usecase
This app serves the usecase of testing the pip package, specifically all communication methods that are available. Furtheremore, SMPC, DP, different datatypes and 
using or not using a memo are tested. 

# Description
Tests are choosen randomly, the number of tests can be changed. All settings 
are hardcoded as constants at the start of the app and the app must be rebuilt 
if settings want to be changed.
If a test fails, the log will contain the line TEST FAILED: with more information
afterwards. As e.g. broadcasting and p2p are also tested, the TEST FAILED line
might be in the log of the coordinator or in the log of any client.
The easiest is to gather all logs in one folder and simply search with
```
grep -r "TEST F"
```
