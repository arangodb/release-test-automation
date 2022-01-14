
(function () {
  let big_doc = '';
  if (options.bigDoc) {
    for (let i=0; i < 100000; i++) {
      big_doc += "abcde" + i;
    }
  }
  return {
    isSupported: function(version, oldVersion, options, enterprise, cluster) {
      return true;
    },

    makeDataDB: function(options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      print(`making per database data ${dbCount}`);
    },
    makeData: function(options, isCluster, isEnterprise, dbCount, loopCount) {
      // All items created must contain dbCount and loopCount
      print(`making data ${dbCount} ${loopCount}`);
      let G = createSafe(`G_naive_${loopCount}`, graphName => {
        return g._create(graphName,
                         [
                           g._relation(`citations_naive_${loopCount}`,
                                       [`patents_naive_${loopCount}`],
                                       [`patents_naive_${loopCount}`])
                         ],
                         [],
                         {
                           replicationFactor: getReplicationFactor(2),
                           numberOfShards:getShardCount(3)
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
    checkData: function(options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbConut} ${loopCount}`);
    // Check graph:

      let patents_naive = db._collection(`patents_naive_${loopCount}`)
      if (patents_naive.count() !== 761) { throw "Orange"; }
      progress();
      let citations_naive = db._collection(`citations_naive_${loopCount}`)
      if (citations_naive.count() !== 1000) { throw "Papaya"; }
      progress();
      if (db._query(`FOR v, e, p IN 1..10 OUTBOUND "${patents_naive.name()}/US:3858245${loopCount}"
                 GRAPH "G_naive_${loopCount}"
                 RETURN v`).toArray().length !== 6) { throw "Physalis"; }
      progress();
    },
    clearData: function(options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbConut} ${loopCount}`);
      // Drop graph:

      let g = require("@arangodb/general-graph");
      progress();
      try { g._drop(`G_naive_${ccount}`, true); } catch(e) { }
    }
  };

}())
