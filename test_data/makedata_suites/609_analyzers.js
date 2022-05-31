/* global print */

(function () {
  const a = require("@arangodb/analyzers");
  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      let currentVersionSemver = semver.parse(semver.coerce(currentVersion));
      let oldVersionSemver = semver.parse(semver.coerce(oldVersion));
      return semver.gte(currentVersionSemver, "3.9.0") && semver.gte(oldVersionSemver, "3.9.0");
    },

    makeDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      print(`making per database data ${dbCount}`);
      progress('create n-gram analyzer');
      let analyzerName = `trigram_${dbCount}`

      let trigram = createSafe(analyzerName,
        analyzer => {
          return a.save(`${analyzerName}`, "ngram", { min: 3, max: 3, preserveOriginal: false, streamType: "utf8" }, ["frequency", "norm", "position"]);
        }, analyzer => {
          return a.analyzer(`trigram_0`);
        });
    },
    makeData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
      // All items created must contain dbCount and loopCount
      print(`making data ${dbCount} ${loopCount}`);
    },
    checkDataDB: function (options, isCluster, isEnterprise, dbCount, readOnly) {
      print(`checking data ${dbCount}`);
      // Check analyzer:  analyzers.analyzer("trigram").properties();
      let analyzerName = `trigram_${dbCount}`
      print(`Listing all analyzers in current database`)
      a.toArray();

      print(`Checking number of analyzer is correct`)
      if (a.toArray().length !== 14) {
        throw new Error("Analyzer not created!");
      }
      progress();

      if (a.analyzer("trigram_0") == null) {
        throw new Error("Analyzer not found!");
      }

      print(`Create and use a trigram Analyzer with preserveOriginal disabled:`)
      db._query(`RETURN TOKENS("foobar", "trigram_0")`).toArray();

      print(`Checking trigram analyzer properties.`)
      a.analyzer(`trigram_0`).properties();
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
    },

    clearDataDB: function (options, isCluster, isEnterprise, dbCount, database) {
      print(`checking data ${dbCount} ${loopCount}`);

      let analyzerName = `trigram_${dbCount}`
      print(`analyzer name: ${analyzerName}`)

      try {
        const array = a.toArray();
        for (let i = 0; i < array.length; i++) {
          const name = array[i];
          if (name == `trigram_0`) {
            a.remove(`trigram_0`);
          }
        }
      } catch (e) {
        print(e);
      }
      progress();
    },
    clearData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
      print(`checking data ${dbCount} ${loopCount}`);
    }
  };

}());
