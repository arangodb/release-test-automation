/*jshint globalstrict:false, strict:false, unused: false */
/*global assertEqual, assertTrue, arango, print, ARGUMENTS */

var jsunity = require("jsunity");


function SyncCheckSuite() {
  'use strict';
  return {

    setUp: function() {
    },

    tearDown: function() {
    },

    testCollectionInSync: function() {
      let colInSync=true;
      do {
        colInSync=true;
        let countInSync = 0;
        let countStillWaiting = 0;
        arango.GET('/_api/replication/clusterInventory').collections.forEach(col => {
          colInSync &= col.allInSync;
          if (!col.allInSync) {
            print("not in sync: ");
            print(col);
            countStillWaiting += 1
          } else {
            countInSync+= 1;
          }
        });
        require('internal').sleep(1);
        print(`In Sync: ${countInSync} Still Waiting: ${countStillWaiting}`);
      } while (!colInSync);
    }
  }
}

jsunity.run(SyncCheckSuite);

return jsunity.done();
