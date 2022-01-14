/* global print, db, internal, arango */

/* this handler is here to wait for a cluster to have all shard leaders moved away from a stopped node */

(function () {
  return {
    isSupported: function (version, oldVersion, options, enterprise, cluster) {
      return (options.disabledDbserverUUID !== "");
    },
    checkDataDB: function (options, isCluster, isEnterprise, dbCount, readOnly) {
      print(`checking data ${dbCount}`);
      let count = 0;
      let collections = [];
      print("waiting for all shards on " + options.disabledDbserverUUID + " to be moved");
      while (count < 500) {
        collections = [];
        let found = 0;
        db._collections().map((c) => c.name()).forEach((c) => {
          let shards = db[c].shards(true);
          Object.values(shards).forEach((serverList) => {
            if (serverList.length > 0 && serverList[0] === options.disabledDbserverUUID) {
              ++found;
              collections.push(c);
            }
          });
        });
        if (found > 0) {
          print(found + ' found - Waiting - ' + JSON.stringify(collections));
          internal.sleep(1);
          count += 1;
        } else {
          break;
        }
      }
      if (count > 499) {
        let collectionData = "Still have collections bound to the failed server: ";
        collections.forEach(col => {
          print(col);
          collectionData += "\n" + JSON.stringify(col) + ":\n" +
            JSON.stringify(db[col].shards(true)) + "\n" +
            JSON.stringify(db[col].properties());
        });
        print(collectionData);
        throw("Still have collections bound to the failed server: " + JSON.stringify(collections));
      }
      let shardDist = {};
      count = 0;
      print("waiting for all new leaders to assume leadership");
      while (count < 500) {
        collections = [];
        let found = 0;
        let shardDist = arango.GET("/_admin/cluster/shardDistribution");
        if (shardDist.code !== 200 || typeof shardDist.results !== "object") {
          continue;
        }
        let cols = Object.keys(shardDist.results);
        cols.forEach((c) => {
          let col = shardDist.results[c];
          let shards = Object.keys(col.Plan);
          shards.forEach((s) => {
            if (col.Plan[s].leader !== col.Current[s].leader) {
              ++found;
              collections.push([c, s]);
            }
          });
        });
        if (found > 0) {
          print(found + ' found - Waiting - ' + JSON.stringify(collections));
          internal.sleep(1);
          count += 1;
        } else {
          break;
        }
      }
      if (count > 499) {
        let collectionData = "Still have collections with incomplete failover: ";
        collections.forEach(col => {
          print(col);
          let shardDistInfoForCol = "";
          if (shardDist.hasOwnProperty("results") &&
              shardDist.results.hasOwnProperty(col)) {
            shardDistInfoForCol = JSON.stringify(shardDist.results[col]);
          }
          collectionData += "\n" + JSON.stringify(col) + ":\n" +
            JSON.stringify(db[col].shards(true)) + "\n" +
            JSON.stringify(db[col].properties()) + "\n" +
            shardDistInfoForCol;
        });
        print(collectionData);
        throw new Error("Still have collections with incomplete failover: " + JSON.stringify(collections));
      }

      print("done - continuing test.");
    }
  };
}());
