/* global print */
/*jslint maxlen: 130 */

(function () {
  const a = require("@arangodb/analyzers");
  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise) {
      let currentVersionSemver = semver.parse(semver.coerce(currentVersion));
      let oldVersionSemver = semver.parse(semver.coerce(oldVersion));
      return semver.gt(currentVersionSemver, "3.8.0") && semver.lt(oldVersionSemver, "3.8.100");
    },

    makeDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      print(`making per database data ${dbCount}`);
      progress("create pipeline analyzer");
      let analyzerName = `pipeline_${dbCount}`;
      let trigram = createSafe(analyzerName,
        function () {
          return a.save(`${analyzerName}`, "pipeline", { pipeline: [{ type: "norm", properties: { locale: "en.utf-8", case: "upper" } },{ type: "ngram", properties: {
              min: 2, max: 2, preserveOriginal: false, streamType: "utf8" } }] }, ["frequency", "norm", "position"]);
        }, function () {
          if (a.analyzer(analyzerName) === null){
            throw new Error("Analyzer creation failed!");
          }
        });
    },
    checkDataDB: function (options, isCluster, isEnterprise, dbCount, readOnly) {
      print(`checking data ${dbCount}`);
      // checking analyzer's name
      let testName = a.analyzer(`pipeline_0`).name();
      let expectedName = "_system::pipeline_0";
      if (testName !== expectedName){
        throw new Error("Analyzer name not found!");
      }
      progress();

      //checking analyzer's type
      let testType = a.analyzer("pipeline_0").type();
      let expectedType = "pipeline";
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
    };

      let testProperties = a.analyzer("pipeline_0").properties();
      let expectedProperties = {
        "pipeline" : [
          {
            "type" : "norm",
            "properties" : {
              "locale" : "en.utf-8",
              "case" : "upper",
              "accent" : true
            }
          },
          {
            "type" : "ngram",
            "properties" : {
              "min" : 2,
              "max" : 2,
              "preserveOriginal" : false,
              "streamType" : "utf8"
            }
          }
        ]
      };

      checkProperties(testProperties, expectedProperties);
      progress();

      if (a.analyzer("pipeline_0") === null) {
        throw new Error("Analyzer not found!");
      }

      function arraysEqual(a, b) {
        if ((a === b) && (a === null || b === null) && (a.length !== b.length)){
          throw new Error("Didn't get the expected response from the server!");
        }
      }

      let myArray = [
        [
          "QU",
          "UI",
          "IC",
          "CK",
          "K ",
          " B",
          "BR",
          "RO",
          "OW",
          "WN",
          "N ",
          " F",
          "FO",
          "OX"
        ]
      ];

      // print(`Create and use a pipeline Analyzer with preserveOriginal disabled:`)
      let pipelineArray = db._query(`RETURN TOKENS("Quick brown foX", "pipeline_0")`).toArray();
      arraysEqual(myArray, pipelineArray);
    },
    clearDataDB: function (options, isCluster, isEnterprise, dbCount, database) {
      print(`checking data ${dbCount}`);
      try {
        const array = a.toArray();
        for (let i = 0; i < array.length; i++) {
            const name = array[i];
            if (name == `pipeline_${dbCount}`) {
                a.remove(`pipeline_${dbCount}`);
            }
        }
        // checking created analyzer is deleted or not
        if (a.analyzer(`pipeline_${dbCount}`) != null) {
          throw new Error("pipeline_0 analyzer isn't deleted yet!");
        }
      } catch (e) {
        print(e);
      }
      progress();
    }
  };

}());
