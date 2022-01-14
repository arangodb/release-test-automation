/* global fs, PWD, writeGraphData, getShardCount,getReplicationFactor,  print, progress, db, createSafe, _  */

(function () {
  const g = require('@arangodb/general-graph');
  let vertices = JSON.parse(fs.readFileSync(`${PWD}/vertices.json`));
  let edges = JSON.parse(fs.readFileSync(`${PWD}/edges_naive.json`));
  return {
    isSupported: function (version, oldVersion, options, enterprise, cluster) {
      return true;
    },
    makeData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
      // All items created must contain dbCount and loopCount
      print(`making data ${dbCount} ${loopCount}`);
      createSafe(`G_naive_${loopCount}`, graphName => {
        return g._create(graphName,
                         [
                           g._relation(`citations_naive_${loopCount}`,
                                       [`patents_naive_${loopCount}`],
                                       [`patents_naive_${loopCount}`])
                         ],
                         [],
                         {
                           replicationFactor: getReplicationFactor(2),
                           numberOfShards: getShardCount(3)
                         });

      }, graphName => {
        return g._graph(graphName);
      });
      progress('createGraph1');
      writeGraphData(db._collection(`patents_naive_${loopCount}`),
                     db._collection(`citations_naive_${loopCount}`),
                     _.clone(vertices), _.clone(edges));
      progress('loadGraph1');
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
    // Check graph:

      let patentsNaive = db._collection(`patents_naive_${loopCount}`);
      if (patentsNaive.count() !== 761) {
        throw new Error("Orange");
      }
      progress();
      let citationsNaive = db._collection(`citations_naive_${loopCount}`);
      if (citationsNaive.count() !== 1000) {
        throw new Error("Papaya");
      }
      progress();
      if (db._query(`FOR v, e, p IN 1..10 OUTBOUND "${patentsNaive.name()}/US:3858245${loopCount}"
                 GRAPH "G_naive_${loopCount}"
                 RETURN v`).toArray().length !== 6) {
        throw new Error("Physalis");
      }
      progress();
    },
    clearData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
      // Drop graph:
      progress();
      try {
        g._drop(`G_naive_${loopCount}`, true);
      } catch (e) { }
    }
  };
}());
