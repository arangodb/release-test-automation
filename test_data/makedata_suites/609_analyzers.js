/* global print, semver, progress, createSafe, db */
/*jslint maxlen: 130 */

(function () {
  const a = require("@arangodb/analyzers");
  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      let currentVersionSemver = semver.parse(semver.coerce(currentVersion));
      let oldVersionSemver = semver.parse(semver.coerce(oldVersion));
      return semver.gte(oldVersionSemver, "3.9.0");
    },

    makeDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      print(`making per database data ${dbCount}`);
      progress("create trigram analyzer");
      let analyzerName = `trigram_${dbCount}`;
      let trigram = createSafe(analyzerName,
        function () {
          return a.save(`${analyzerName}`, "ngram", { min: 3, max: 3, preserveOriginal: false, streamType: "utf8" }, ["frequency", "norm", "position"]);
        }, function () {
          if (a.analyzer(analyzerName) === null){
            throw new Error("Analyzer creation failed!");
          }
        });
      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      print(`checking data ${dbCount}`);
      // checking analyzer's name
      let analyzerName = `trigram_${dbCount}`;
      if (a.analyzer(analyzerName) === null) {
        throw new Error(`Analyzer ${analyzerName} not found!`);
      }

      let testName = a.analyzer(analyzerName).name();
      let expectedName = `_system::trigram_${dbCount}`;
      if (testName !== expectedName){
        throw new Error(`Analyzer name of ${analyzerName} not found!`);
      }
      progress();

      //checking analyzer's type
      let testType = a.analyzer(analyzerName).type();
      let expectedType = "ngram";
      if (testType !== expectedType){
        throw new Error(`Analyzer ${analyzerName} type missmatched!`);
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
          throw new Error(`Analyzer type ${analyzerName} missmatched!`);
        }
      };

      let testProperties = a.analyzer(analyzerName).properties();
      let expectedProperties = {
          "min" : 2,
          "max" : 3,
          "preserveOriginal" : true,
          "streamType" : "binary",
          "startMarker" : "~",
          "endMarker" : "!"
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
          "foo",
          "oob",
          "oba",
          "bar"
        ]
      ];
      let trigramArray = db._query(`RETURN TOKENS("foobar", "${analyzerName}")`).toArray();

      arraysEqual(myArray, trigramArray);
      return 0;
    },
    clearDataDB: function (options, isCluster, isEnterprise, dbCount, database) {
      print(`checking data ${dbCount}`);
      try {
        const array = a.toArray();
        for (let i = 0; i < array.length; i++) {
          const name = array[i];
          if (name === `trigram_${dbCount}`) {
            a.remove(`trigram_${dbCount}`);
          }
        }
        // checking created analyzer is deleted or not
        if (a.analyzer(`trigram_${dbCount}`) !== null) {
          throw new Error("trigram_0 analyzer isn't deleted yet!");
        }
      } catch (e) {
        print(e);
      }
      progress();
      return 0;
    },
  };

}());
