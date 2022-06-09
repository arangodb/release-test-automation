/* global print */
/*jslint maxlen: 130 */

(function () {
  const a = require("@arangodb/analyzers");
  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      let currentVersionSemver = semver.parse(semver.coerce(currentVersion));
      let oldVersionSemver = semver.parse(semver.coerce(oldVersion));
      return semver.gt(currentVersionSemver, "3.7.0") && semver.lt(oldVersionSemver, "3.7.100");
    },

    makeDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      print("making per database data ${dbCount}");
      progress("create pipeline analyzer");
      let analyzerName = `text_${dbCount}`;
      let text = createSafe(analyzerName,
        function () {
          return a.save(`${analyzerName}`, "text", {locale: "el.utf-8",
          stemming: true,
          case: "lower",
          accent: false,
          stopwords: []
        }, ["frequency", "norm", "position"]);
        }, function () {
          return a.analyzer(`text_0`);
        });
    },
    checkDataDB: function (options, isCluster, isEnterprise, dbCount, readOnly) {
      print(`checking data ${dbCount}`);
      print(`Listing all analyzers in current database`);
      a.toArray();
      print(`Checking number of analyzer is correct`);
      if (a.toArray().length !== 14) {
        throw new Error("Analyzer not created!");
      }
      progress();

      if (a.analyzer("text_0") == null) {
        throw new Error("Analyzer not found!");
      }

      function arraysEqual(a, b) {
        if ((a === b) && (a == null || b == null) && (a.length !== b.length)){
          throw new Error("Didn't get the expected response from the server!");
        }
      }

      let myArray =[
        [
          "crazy",
          "fast",
          "nosql",
          "database"
        ]
      ];

      // print(`Create and use a text Analyzer with preserveOriginal disabled:`)
      let textArray = db._query(`RETURN TOKENS("Crazy fast NoSQL-database!", "text_0")`).toArray();
      arraysEqual(myArray, textArray);
    },
    clearDataDB: function (options, isCluster, isEnterprise, dbCount, database) {
      print(`checking data ${dbCount}`);
      try {
        const array = a.toArray();
        for (let i = 0; i < array.length; i++) {
          const name = array[i];
          if (name == `text_0`) {
            a.remove(`text_0`);
          }
        }
        // checking created analyzer is deleted or not
        if (a.analyzer("text_0") != null) {
          throw new Error("text_0 analyzer isn't deleted yet!");
        }
      } catch (e) {
        print(e);
      }
      progress();
    },
  };

}());
