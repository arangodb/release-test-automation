/* global fs, PWD, writeGraphData, getShardCount, getReplicationFactor,  print, progress, db, createSafe, _, semver */

(function () {
  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      let current = semver.parse(semver.coerce(currentVersion));

      return semver.gte(current, "3.9.0") && cluster && !options.readOnly && enterprise;
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      // depends on the 550_enterprise_graph.js to be there
      print(`checking data ${dbCount} ${loopCount}`);
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
  };
}());
