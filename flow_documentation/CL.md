==== Active Failover Scenario ===
- Supported on: All Targets
- Hot-backup: True

### Cluster

 - [ ] Start a 3 nodes cluster (if the test is executed on a single machine, please start at least 3 _Starter_ instances using the option `--starter.data-dir` to use 3 different local directories. Use option `--server.storage-engine=rocksdb`). Use a JWT authentication to be more close to a real use case scenario - You may find useful the following _Starter_ commands:
    - `arangodb --starter.data-dir=<path-to-your-data-dir>\node1 --auth.jwt-secret <path-to-your-jwt-secret>`
    - `arangodb --starter.data-dir=<path-to-your-data-dir>\node2 --starter.join 127.0.0.1 --auth.jwt-secret <path-to-your-jwt-secret>`
    - `arangodb --starter.data-dir=<path-to-your-data-dir>\node3 --starter.join 127.0.0.1 --auth.jwt-secret <path-to-your-jwt-secret>` 
 - [ ] Try to add a new node *without* specifying the JWT-secret using the following command: `arangodb --starter.data-dir=<path-to-your-data-dir>\node4 --starter.join 127.0.0.1` - You should *not* be able to do that
    
 - [ ] Quickly verify that the cluster is up an running by accessing the UI
 - [ ] Create some collections from one node and check if they are correctly replicated (all shards) into the other nodes (depending on the RF that was set)
 - [ ] Shutdown one _Starter_ instance and quickly verify that the Cluster is up an running by accessing the UI
 - [ ] Bring that _Starter_ instance up again and quickly verify that all 3 nodes are correctly up and running by accessing the UI 
 - [ ] Bring another _Starter_ instance down and quickly verify that the cluster is up an running by accessing the UI

