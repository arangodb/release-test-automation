==== Leader Follower Replication Scenario ===
- Supported on: All Targets
- Hot-backup: False



 - Start two single instances using the following commands: 
    - `arangodb --starter.data-dir=<path-to-your-data-dir>/leader --starter.mode single --starter.port XXXX`
    - `arangodb --starter.data-dir=<path-to-your-data-dir>/follower --starter.mode single --starter.port YYYY`
 - From _arangosh_ connect to your _Follower_ instance using the following command: `arangosh --server.endpoint tcp://IP:YYYY` - you should be asked to pass a password (if no password was specified then leave it blank)
    -  Pass the following command to make the replication copy the initial data from the _Master_ to the _Slave_ and start the continuous replication on the _Slave_ (where `IP:XXXX` is the endpoing of _Master_):
        ```
        require("@arangodb/replication").setupReplicationGlobal({
            endpoint: "tcp://IP:XXXX",
            username: "myuser",
            password: "mypasswd",
            verbose: false,
            includeSystem: true,
            incremental: true,
            autoResync: true
            });
        ```
    
 - [ ] Verify that the Replication tab (shown on the left side in the UI) is reporting the correct replication method (Master Slave) from both of _Master_ and _Slave_ UI instances 
 - [ ] Create some collections from the _Master_ instance and check if they are correctly replicated into the _Slave_ instance (it may take some time to completely replicate since it's an async-replication)```

