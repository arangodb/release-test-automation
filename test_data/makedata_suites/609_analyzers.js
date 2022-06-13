/* global print */
/*jslint maxlen: 100 */

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
      progress("create n-gram analyzer");
      let analyzerName = `trigram_${dbCount}`;
      let trigram = createSafe(analyzerName,
        function () {
          return a.save(`${analyzerName}`, "ngram", { min: 3, max: 3, preserveOriginal: false, streamType: "utf8" }, ["frequency", "norm", "position"]);
        }, function () {
          return a.analyzer(`trigram_0`);
        });
    },
    checkDataDB: function (options, isCluster, isEnterprise, dbCount, readOnly) {
      print(`checking data ${dbCount}`);
      // checking analyzer's name
      let testName = a.analyzer("trigram_0").name();
      let expectedName = "_system::trigram_0";
      if (testName !== expectedName){
        throw new Error("Analyzer name not found!");
      }
      progress();

      //checking analyzer's type
      let testType = a.analyzer("trigram_0").type();
      let expectedType = "ngram";
      if (testType !== expectedType){
        throw new Error("Analyzer type missmatched!");
      }
      progress();

      //checking analyzer's properties
      const checkProperties = function(obj1, obj2) {
        const obj1Length = Object.keys(obj1).length;
        const obj2Length = Object.keys(obj2).length;

        if(obj1Length === obj2Length) {
            return Object.keys(obj1).every(
                (key) => obj2.hasOwnProperty(key)
                   && obj2[key] === obj1[key]);
        }else{
          throw new Error("Analyzer type missmatched!");
        }
    }

      let testProperties = a.analyzer("trigram_0").properties();
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

      if (a.analyzer("trigram_0") === null) {
        throw new Error("Analyzer not found!");
      }

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
      let trigramArray = db._query(`RETURN TOKENS("foobar", "trigram_0")`).toArray();

      arraysEqual(myArray, trigramArray);
    },
    clearDataDB: function (options, isCluster, isEnterprise, dbCount, database) {
      print(`checking data ${dbCount}`);
      try {
        const array = a.toArray();
        for (let i = 0; i < array.length; i++) {
          const name = array[i];
          if (name === `trigram_0`) {
            a.remove(`trigram_0`);
          }
        }
        // checking created analyzer is deleted or not
        if (a.analyzer("trigram_0") !== null) {
          throw new Error("trigram_0 analyzer isn't deleted yet!");
        }
      } catch (e) {
        print(e);
      }
      progress();
    },
  };

}());
