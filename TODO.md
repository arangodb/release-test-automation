- [x] 5h DC2DC
- [x] ?? windows starter (starter needs to be fixed)
- [x] 3h rpm install (..) [Found bug: default password doesn't work if system has a ready existing database. Impl to check this done, commented out] 
- [x] ?? macos support for dmgs (.)
- [x] 8h pylint/pylama
- [x] 4h check package integrity and binaries
- [ ] 8h testdata integration (.)
- [ ] 2x 4h conflict checking in packages
- [ ] 2x 2h test debug packages
- [ ] upgrade of cases
  - [x] debian
  - [x] rpm
  - [ ] mac
  - [ ] nsis
  - [x] 8h active failover
  - [x] 8h cluster
  - [ ] 8h DC2DC (....) (starter doesn't kill syncer that it didn't spawn)
- [ ] ?? better reporting (more than true/false)
- [x] ?? improve error handling in installers for non-clean systems (....)
- [ ] ?? improve error handling (catch exceptions, make messages) (..)
- [ ] ?? frontend testing?
- [ ] FTP Download from -   ftp://nas02.arangodb.biz/buildfiles - Explore directory structure in interactive client, Create attic-test-script. Copy package name calculation routines from the installers, use https://docs.python.org/3/library/ftplib.html to download. Check for windows compatibility. Use QA-Centos VM for this. 
- [ ] validate makedata 
  - [ ] system install
  - [ ] leader follower
  - [ ] active failover
  - [ ] cluster
  - [ ] dc2dc (pending to fix dc2dc)
- [ ] cluster case: kill all but agency to keep the UI and RAFT still responsive, kill agent after test, and respawn full instance afterwards
        #  TODO self.create_test_collection
        logging.info("stopping instance 2")
        self.starter_instances[2].terminate_instance()
     Alternative: 4 starters, so the agency may remain in size 3? 
- [ ] terminate starter - check that it also terminated all arangods / sync'ers
- [ ] click recepie integration - when prompting the user, tell him what to check in the webui
- [ ] refactoring
  - [ ] instance - this is to widely used, should be more dependent on whats done.
  - [ ] startermanager.py - ArangodInstance() own file + add release_tester/arangodb/log.py there
- [ ] timeout in afo: `11:56:25 INFO activefailover.py:124 - waiting for new leader...`
- [x] validate arangosh exits non-zero on error
