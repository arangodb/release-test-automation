/* global print, progress, createCollectionSafe, db, createSafe  */

(function () {
    const a = require("@arangodb/analyzers");
    return {
        isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
          let currentVersionSemver = semver.parse(semver.coerce(currentVersion));
          let oldVersionSemver = semver.parse(semver.coerce(oldVersion));
          return semver.gte(currentVersionSemver, "3.9.0") && semver.gte(oldVersionSemver, "3.9.0");
        },

    makeData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
      // All items created must contain dbCount and loopCount
      print(`making data ${dbCount} ${loopCount}`);
      progress('create n-gram analyzer');
      let analyzer1 = `ngram_${loopCount}`;
      let ngram = createSafe(analyzer1,
                             analyzer => {
                               return a.save("trigram", "ngram", {min: 3, max: 3, preserveOriginal: false, streamType: "utf8"}, ["frequency", "norm", "position"]);
                             }, analyzer => {
                               return a.analyzer('trigram');
                             }
                            );
    },

    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
      // Check analyzer:  analyzers.analyzer("trigram").properties();
      let analyzer1 = `ngram_${loopCount}`;
      print(`Listing all analyzers in current database`)
      a.toArray();

      print(`Checking number of analyzer is correct`)
      if (a.toArray().length !== 14) {
        throw new Error("Analyzer");
      }
      progress();
      
      print(`Create and use a trigram Analyzer with preserveOriginal disabled:`)
      db._query(`RETURN TOKENS("foobar", "trigram")`).toArray();
      
      print(`Checking trigram analyzer properties.`)
      a.analyzer("_system::trigram").properties();
    },

    clearData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
      try {
        a.remove("trigram");
      } catch (e) {
        print(e);
      }
      progress();
    }
  };
}());