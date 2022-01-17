/* global fs, PWD, writeGraphData, getShardCount, getReplicationFactor,  print, progress, db, createSafe, _, semver */

(function () {
  let gsm;
  let checkSmartGraphValidator;
  let vertices = JSON.parse(fs.readFileSync(`${PWD}/vertices.json`));
  let smartEdges = JSON.parse(fs.readFileSync(`${PWD}/edges.json`));

  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      let current = semver.parse(semver.coerce(currentVersion));

      checkSmartGraphValidator = semver.gte(current, "3.9.0") && cluster && !options.readOnly;
      checkSmartGraphValidator = false; // TODO!
      if (enterprise) {
        gsm = require('@arangodb/smart-graph');
      }
      return enterprise;
    },
    makeData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
      // All items created must contain dbCount and loopCount
      print(`making data ${dbCount} ${loopCount}`);
      // And now a smart graph (if enterprise):
      createSafe(`G_smart_${loopCount}`, graphName => {
        return gsm._create(graphName,
                           [
                             gsm._relation(`citations_smart_${loopCount}`,
                                           [`patents_smart_${loopCount}`],
                                           [`patents_smart_${loopCount}`])],
                           [],
                           {
                             numberOfShards: getShardCount(3),
                             replicationFactor: getReplicationFactor(2),
                             smartGraphAttribute: "COUNTRY"
                           });
      }, graphName => {
        return gsm._graph(graphName);
      });
      progress('createEGraph2');
      writeGraphData(db._collection(`patents_smart_${loopCount}`),
                     db._collection(`citations_smart_${loopCount}`),
                     _.clone(vertices),
                     _.clone(smartEdges));
      progress('writeEGraph2');
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
      const vColName = `patents_smart_${loopCount}`;
      let patentsSmart = db._collection(vColName);
      if (patentsSmart.count() !== 761) {
        throw new Error("Cherry");
      }
      progress();
      const eColName = `citations_smart_${loopCount}`;
      let citationsSmart = db._collection(eColName);
      if (citationsSmart.count() !== 1000) {
        throw new Error("Liji");
      }
      progress();
      const gName = `G_smart_${loopCount}`;
      if (db._query(`FOR v, e, p IN 1..10 OUTBOUND "${patentsSmart.name()}/US:3858245${loopCount}"
                   GRAPH "${gName}"
                   RETURN v`).toArray().length !== 6) {
        throw new Error("Black Currant");
      }
      progress();
      if (checkSmartGraphValidator) {
        try {
          const vColName = `patents_smart_${loopCount}`;
          const eColName = `citations_smart_${loopCount}`;
          const gName = `G_smart_${loopCount}`;
          const remoteDocument = {
            _key: "abc:123:def",
            _from: `${vColName}/abc:123`,
            _to: `${vColName}/def:123`
          };
          const localDocument = {
            _key: "abc:123:abc",
            _from: `${vColName}/abc:123`,
            _to: `${vColName}/abc:123`
          };
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
              if (e.errorNum !== 1466 && e.errorNum !== 1233) {
                return {
                  fail: true,
                  message: `Validator of collection ${colName} on atempt to store ${doc} returned unexpected error ${JSON.stringify(e)}`
                };
              }
            }
            return {fail: false};
          };
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
    clearData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
    // Drop graph:
      let gsm = require("@arangodb/smart-graph");
      progress();
      try {
        gsm._drop(`G_smart_${loopCount}`, true);
      } catch (e) { }
    }
  };
}());
