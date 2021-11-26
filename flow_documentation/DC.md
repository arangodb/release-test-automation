==== DC2DC Scenario ===
- Supported on: All Targets but Windows
- Hot-backup: True

### DC2DC (check only as Primary or Secondary cluster)

 - [ ] Use the following [procedure](https://github.com/arangodb-helper/arangodb/tree/master/examples/local-sync) to deploy a local DC2DC using the _Starter_ 
 - [ ] Quickly verify that both DCs are up an running by accessing their respective UI
 - [ ] Create some collections from the _Primary DC_ and check if they are correctly replicated into the _Replica DC_ (it may take some time to completely replicate since it's an async-replication)  
 - [ ] Stop the replication between the two DCs from the _arangosync_ 
     - [ ] Make some modification from the _Replica DC_ (that now is an independent Cluster) 
     - [ ] Re-establish the replication between the two DCs
     - [ ] Check if all changes done on the _Replica DC_ are now discarded 
 - [ ] Change the replication direction from the _Replica DC_ to the _Primary DC_ and check if everything is working properly

## HotBackup
 - [ ] not able to `restore` but able to `create`, `download` and `upload` HotBackup
