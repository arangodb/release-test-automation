/* global print, semver, progress, createSafe, db */
/*jslint maxlen: 100 */

(function () {
  const a = require("@arangodb/analyzers");
  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      let currentVersionSemver = semver.parse(semver.coerce(currentVersion));
      let oldVersionSemver = semver.parse(semver.coerce(oldVersion));
      return semver.gt(oldVersionSemver, "3.7.0");
    },

    makeDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      print(`making per database data ${dbCount}`);
      progress("create text analyzer");
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
          if (a.analyzer(analyzerName) === null) {
            throw new Error("Analyzer creation failed!");
          }
        });
      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      print(`checking data ${dbCount}`);
      progress(`checking data with ${dbCount}`);
      // checking analyzer's name
      let analyzerName = `text_${dbCount}`;
      if (a.analyzer(analyzerName) === null) {
        throw new Error("Analyzer not found!");
      }

      let testName = a.analyzer(analyzerName).name();
      let expectedName = `_system::text_${dbCount}`;
      if (testName !== expectedName) {
        throw new Error(`Analyzer name not found!`);
      }
      progress();

      //checking analyzer's type
      let testType = a.analyzer(analyzerName).type();
      let expectedType = "text";
      if (testType !== expectedType){
        throw new Error("Analyzer type missmatched!");
      }
      progress();

      //checking analyzer's properties
      const checkProperties = function(obj1, obj2) {
        const obj1Length = Object.keys(obj1).length;
        const obj2Length = Object.keys(obj2).length;

        if (obj1Length === obj2Length) {
            return Object.keys(obj1).every(
                (key) => obj2.hasOwnProperty(key)
                   && obj2[key] === obj1[key]);
        } else {
          throw new Error("Analyzer type missmatched!");
        }
      };

      let testProperties = a.analyzer(analyzerName).properties();
      let expectedProperties = {
        "locale" : "el.utf-8",
        "case" : "lower",
        "stopwords" : [ ],
        "accent" : false,
        "stemming" : true
      };

      checkProperties(testProperties, expectedProperties);
      progress();

      function arraysEqual(a, b) {
        if ((a === b) && (a === null || b === null) && (a.length !== b.length)){
          throw new Error("Didn't get the expected response from the server!");
        }
      }

      let myArray = [
        [
          "crazy",
          "fast",
          "nosql",
          "database"
        ]
      ];

      // print(`Create and use a text Analyzer with preserveOriginal disabled:`)
      let textArray = db._query(`RETURN TOKENS("Crazy fast NoSQL-database!", "${analyzerName}")`).toArray();
      arraysEqual(myArray, textArray);
      return 0;
    },
    clearDataDB: function (options, isCluster, isEnterprise, dbCount, database) {
      print(`checking data ${dbCount}`);
      try {
        const array = a.toArray();
        for (let i = 0; i < array.length; i++) {
          const name = array[i];
          if (name === `text_${dbCount}`) {
            a.remove(`text_${dbCount}`);
          }
        }
        // checking created analyzer is deleted or not
        if (a.analyzer(`text_${dbCount}`) != null) {
          throw new Error("text_0 analyzer isn't deleted yet!");
        }
      } catch (e) {
        print(e);
      }
      progress();
      return 0;
    },
  };

}());
