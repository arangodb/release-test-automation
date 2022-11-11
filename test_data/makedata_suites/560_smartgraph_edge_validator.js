/* global fs, PWD, writeGraphData, getShardCount, getReplicationFactor,  print, progress, db, createSafe, _, semver */

(function () {
  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      let current = semver.parse(semver.coerce(currentVersion));

      return semver.gte(current, "3.9.0") && cluster && !options.readOnly;
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      // depends on the 550_enterprise_graph.js to be there
      print(`checking data ${dbCount} ${loopCount}`);
      const ArangoError = require('@arangodb').ArangoError;

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
            throw new Error(`The smartGraph "${gName}" was not created correctly, collection ${colName} missing`);
          }
          try {
            col.save(doc);
            throw new Error(`Validator did not trigger on collection ${colName} stored illegal document`);
          } catch (e) {
            // We only allow the following two errors, all others should be reported.
            if (e instanceof ArangoError) {
              if (e.errorNum !== 1466 &&
                  e.errorNum !== 1233) {
                throw new Error(`Validator of collection ${colName} on atempt to store ${doc} returned unexpected error: ${e.errorNum} - ${e.message}`)
              }
            } else {
              throw(e);
            }
          }
        };
        // We try to insert a document into the wrong shard. This should be rejected by the internal validator
        testValidator(`_local_${eColName}`, remoteDocument);
        testValidator(`_from_${eColName}`, localDocument);
        testValidator(`_to_${eColName}`, localDocument);
      } finally {
        // Always report that we tested SmartGraph edge Validators
        progress("Tested SmartGraph edge validators");
      }
    }
  };
}());
