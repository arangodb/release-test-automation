==== Active Failover Scenario ===
- Supported on: All Targets
- Hot-backup: True


 - [ ] Start an Active Failover Deployment (if the test is executed on a single machine, please start at least 3 Starter instances using the option `--starter.data-dir` to use 3 different local directories). Use a JWT authentication if possible to be more close to a real use case scenario. You may find useful the following _Starter_ commands: 
    - `arangodb --starter.data-dir=<path-to-your-data-dir>\node1 --starter.mode=activefailover`
    - `arangodb --starter.data-dir=<path-to-your-data-dir>\node2 --starter.join 127.0.0.1 --starter.mode=activefailover`
    - `arangodb --starter.data-dir=<path-to-your-data-dir>\node3 --starter.join 127.0.0.1 --starter.mode=activefailover` 
 - [ ] Quickly verify that the _Leader_ instance is accessible from the UI
 - [ ] Quickly verify that the _Followers_ instance are *not* accessible from the UI
 - [ ] Verify that the Replication tab (shown on the left side in the UI) is reporting the correct replication method (Active Failover) 
 - [ ] Verify that the Replication tab (shown on the left side in the UI) is reporting all followers 
 - [ ] Create some collections from the _Leader_ instance 
     - [ ] Shutdown the _Leader_ instance and monitor the re-election of the new _Leader_ instance (from the `arangod.log` and not from the _Starter_ consoles) 
     - [ ] Once a new _Leader_ instance is available check if all collection have been correctly replicated from the previous "killed" Leader 
     - [ ] Bring up again the shut-downed instance (ex-Leader) and check if is now serving as a _Follower_
