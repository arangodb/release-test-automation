
(function () {
  let checkSmartGraphValidator;
  let big_doc = '';
  if (options.bigDoc) {
    for (let i=0; i < 100000; i++) {
      big_doc += "abcde" + i;
    }
  }
  return {
    isSupported: function(currentVersion, oldVersion, options, enterprise, cluster) {
      let current = semver.parse(semver.coerce(currentVersion));

      checkSmartGraphValidator = semver.gte(current, "3.9.0") && cluster;

      return enterprise;
    },

    makeDataDB: function(options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      print(`making per database data ${dbCount}`);
    },
    makeData: function(options, isCluster, isEnterprise, dbCount, loopCount) {
      // All items created must contain dbCount and loopCount
      print(`making data ${dbCount} ${loopCount}`);
      // And now a smart graph (if enterprise):
      let Gsm = createSafe(`G_smart_${loopCount}`, graphName => {
        return gsm._create(graphName,
                           [
                             gsm._relation(`citations_smart_${loopCount}`,
                                           [`patents_smart_${loopCount}`],
                                           [`patents_smart_${loopCount}`])],
                           [],
                           {
                             numberOfShards: getShardCount(3),
                             replicationFactor: getReplicationFactor(2),
                             smartGraphAttribute:"COUNTRY"
                           });
      }, graphName => {
        return gsm._graph(graphName);
      });
      progress('createEGraph2');
      writeGraphData(db._collection(`patents_smart_${loopCount}`),
                     db._collection(`citations_smart_${loopCount}`),
                     _.clone(vertices), _.clone(smart_edges));
      progress('writeEGraph2');
    },
    checkData: function(options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbConut} ${loopCount}`);
      if (false){ // TODO: re-enable me!
        const vColName = `patents_smart_${loopCount}`;
        let patents_smart = db._collection(vColName);
        if (patents_smart.count() !== 761) { throw "Cherry"; }
        progress();
        const eColName = `citations_smart_${loopCount}`;
        let citations_smart = db._collection(eColName);
        if (citations_smart.count() !== 1000) { throw "Liji"; }
        progress();
        const gName = `G_smart_${loopCount}`;
        if (db._query(`FOR v, e, p IN 1..10 OUTBOUND "${patents_smart.name()}/US:3858245${loopCount}"
                   GRAPH "${gName}"
                   RETURN v`).toArray().length !== 6) { throw "Black Currant"; }
        progress();
        const res = testSmartGraphValidator(loopCount);
        if (res.fail) {
          throw res.message;
        }
      }
      if (checkSmartGraphValidator) {
        try {
          const vColName = `patents_smart_${loopCount}`;
          const eColName = `citations_smart_${loopCount}`;
          const gName = `G_smart_${loopCount}`;
          const remoteDocument = {_key: "abc:123:def", _from: `${vColName}/abc:123`, _to: `${vColName}/def:123`};
          const localDocument = {_key: "abc:123:abc", _from: `${vColName}/abc:123`, _to: `${vColName}/abc:123`};
          const testValidator = (colName, doc) => {
            let col = db._collection(colName);
            if (!col) {
              return {
                fail: true,
                message: `The smartGraph "${gName}" was not created correctly, collection ${colName} missing`
              };
            }
            try {
              col.save(doc);
              return {
                fail: true,
                message: `Validator did not trigger on collection ${colName} stored illegal document`
              };
            } catch (e) {
              // We only allow the following two errors, all others should be reported.
              if (e.errorNum != 1466 && e.errorNum != 1233) {
                return {
                  fail: true,
                  message: `Validator of collection ${colName} on atempt to store ${doc} returned unexpected error ${JSON.stringify(e)}`
                };
              }
            }
            return {fail: false};
          }
          // We try to insert a document into the wrong shard. This should be rejected by the internal validator
          let res = testValidator(`_local_${eColName}`, remoteDocument);
          if (res.fail) {
            return res;
          }
          res = testValidator(`_from_${eColName}`, localDocument);
          if (res.fail) {
            return res;
          }
          res = testValidator(`_to_${eColName}`, localDocument);
          if (res.fail) {
            return res;
          }
          return {fail: false};
        } finally {
          // Always report that we tested SmartGraph Validators
          progress("Tested SmartGraph validators");
        }
      }
    },
    clearData: function(options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbConut} ${loopCount}`);
    // Drop graph:

      let g = require("@arangodb/general-graph");
      let gsm = require("@arangodb/smart-graph");
      progress();
      try {
        gsm._drop(`G_smart_${ccount}`, true);
      } catch(e) { }
    }
    }
  };

}())
