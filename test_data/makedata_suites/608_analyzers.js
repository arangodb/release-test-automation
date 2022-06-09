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
          return a.analyzer(`pipeline_0`);
        });
    },
    checkDataDB: function (options, isCluster, isEnterprise, dbCount, readOnly) {
      print(`checking data ${dbCount}`);
      // Check analyzer:  analyzers.analyzer("trigram").properties();
      print(`Listing all analyzers in current database`);
      a.toArray();
      print(`Checking number of analyzer is correct`);
      if (a.toArray().length !== 14) {
        throw new Error("Analyzer not created!");
      }
      progress();

      if (a.analyzer("pipeline_0") == null) {
        throw new Error("Analyzer not found!");
      }

      function arraysEqual(a, b) {
        if ((a === b) && (a == null || b == null) && (a.length !== b.length)){
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
            if (name == `pipeline_0`) {
                a.remove(`pipeline_0`);
            }
        }
        // checking created analyzer is deleted or not
        if (a.analyzer("pipeline_0") != null) {
          throw new Error("pipeline_0 analyzer isn't deleted yet!");
        }
      } catch (e) {
        print(e);
      }
      progress();
    }
  };

}());
