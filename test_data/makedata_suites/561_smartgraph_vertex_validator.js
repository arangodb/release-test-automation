/* global fs, PWD, writeGraphData, getShardCount, getReplicationFactor,  print, progress, db, createSafe, _, semver */

(function () {
  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      let current = semver.parse(semver.coerce(currentVersion));
      return false;
      return semver.gte(current, "3.10.0") && cluster && !options.readOnly;
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      // depends on the 550_enterprise_graph.js to be there
      print(`checking data ${dbCount} ${loopCount}`);
      try {
        const vColName = `patents_smart_${ccount}`;
        const gName = `G_smart_${ccount}`;
        const mismatchedSGAPrefixDoc = {_key: 'NL:1', COUNTRY: 'DE'}
        const missingSGAPrefixDoc = {_key: '1', COUNTRY: 'DE'}

        const vCol = db._collection(vColName);
        if (!vCol) {
          throw new Error(`The smartGraph "${gName}" was not created correctly, collection ${vColName} missing`)
        }

        const testValidator = doc => {
          try {
            vCol.save(doc);
            throw new Error(`Validator did not trigger on collection ${vColName} stored illegal document`);
          } catch (e) {
            // We only allow the following two errors, all others should be reported.
            if (e.errorNum !== 4003 && e.errorNum !== 4001) {
              throw new Error(`Validator of collection ${vColName} on attempt to store ${doc} returned unexpected error ${JSON.stringify(e)}`);
            }
          }
        }

        // We try to insert a document with the wrong key. This should be rejected by the internal validator.
        testValidator(mismatchedSGAPrefixDoc);
        testValidator(missingSGAPrefixDoc);
      } finally {
        // Always report that we tested SmartGraph vertex Validators
        progress("Tested SmartGraph vertex validators");
      }
    }
  };
}());
