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
      // documentation link: https://www.arangodb.com/docs/3.9/analyzers.html

      print(`making per database data ${dbCount}`);
      function createAnalyzer(analyzerName, analyzerCreationQuery){
        // creating analyzer
        let text = createSafe(analyzerName,
          function () {
            return analyzerCreationQuery
          }, function () {
            if (a.analyzer(analyzerName) === null) {
              throw new Error(`${analyzerName} analyzer creation failed!`);
            }
          });
      }

      //collation analyzer properties
      //collation Analyzer for a phonetically similar term search
      let collationEn = `collationEn_${dbCount}`;
      let collationSv = `collationSv_${dbCount}`;

      let aCollationQuery = a.save(`${collationEn}`, "collation", { locale: "en.utf-8" }, ["frequency", "norm", "position"]);
      let bCollationQuery = a.save(`${collationSv}`, "collation", { locale: "sv.utf-8" }, ["frequency", "norm", "position"]);
      var test = db._create("test");
      db.test.save([{ text: "a" },{ text: "å" },{ text: "b" },{ text: "z" },]);
      var view = db._createView("viewEn", "arangosearch", { links: { test: { a: [ collationEn, collationSv ], includeAllFields: true }}});
      var view = db._createView("viewSv", "arangosearch",{ links: { test: { analyzers: [ collationEn, collationSv ], includeAllFields: true }}});

      //creating collation  analyzer
      createAnalyzer(collationEn, aCollationQuery)
      createAnalyzer(collationSv, bCollationQuery)

      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      print(`checking data ${dbCount}`);
      progress(`checking data with ${dbCount}`);

      //This function will check any analyzer's properties
      function checkProperties(analyzer_name, obj1, obj2) {
        const obj1Length = Object.keys(obj1).length;
        const obj2Length = Object.keys(obj2).length;

        if (obj1Length === obj2Length) {
            return Object.keys(obj1).every(
                (key) => obj2.hasOwnProperty(key)
                   && obj2[key] === obj1[key]);
        } else {
          throw new Error(`${analyzer_name} analyzer's type missmatched!`);
        }
      };

      //This function will check any analyzer's equality with expected server response
      function arraysEqual(a, b) {
        if ((a === b) && (a === null || b === null) && (a.length !== b.length)){
          throw new Error("Didn't get the expected response from the server!");
        }
      }

      // this function will check everything regardin given analyzer
      function checkAnalyzer(analyzerName, expectedType, expectedProperties, expectedResult, queryResult){
        if (a.analyzer(analyzerName) === null) {
          throw new Error(`${analyzerName} analyzer creation failed!`);
        }

        //checking analyzer's name
        let testName = a.analyzer(analyzerName).name();
        let expectedName = `_system::${analyzerName}`;
        if (testName !== expectedName) {
          throw new Error(`${analyzerName} analyzer not found`);
        }
        progress();

        //checking analyzer's type
        let testType = a.analyzer(analyzerName).type();
        if (testType !== expectedType){
          throw new Error(`${analyzerName} analyzer type missmatched!`);
        }
        progress();

        //checking analyzer's properties
        let testProperties = a.analyzer(analyzerName).properties();
        checkProperties(analyzerName, testProperties, expectedProperties)

        progress();

        //checking analyzer's query results
        arraysEqual(expectedResult, queryResult);

        progress();
      }

      //-------------------------------collation----------------------------------

      let collationEn = `collationEn_${dbCount}`;
      let collationEnType = "aql";
      let collationEnProperties = {
        "queryString" : "RETURN SOUNDEX(@param)",
        "collapsePositions" : false,
        "keepNull" : true,
        "batchSize" : 10,
        "memoryLimit" : 1048576,
        "returnType" : "string"
      };
      let collationEnExpectedResult =[
        [
          "A652"
        ]
      ];

      let collationEnQueryReuslt = db._query(`RETURN TOKENS("UPPER lower dïäcríticš", "${aqlSoundex}")`).toArray();

      checkAnalyzer(collationEn, collationEnType, collationEnProperties, collationEnExpectedResult, collationEnQueryReuslt)

      return 0;

    },
    clearDataDB: function (options, isCluster, isEnterprise, dbCount, database) {
      print(`checking data ${dbCount}`);
      // deleting analyzer
      function deleteAnalyzer(analyzerName){
        try {
          const array = a.toArray();
          for (let i = 0; i < array.length; i++) {
            const name = array[i];
            if (name === analyzerName) {
              a.remove(analyzerName);
            }
          }
          // checking created text analyzer is deleted or not
          if (a.analyzer(analyzerName) != null) {
            throw new Error(`${analyzerName} analyzer isn't deleted yet!`);
          }
        } catch (e) {
          print(e);
        }
        progress();
      }

      // declaring all the analyzer's name
      let aqlSoundex = `aqlSoundex_${dbCount}`;

      // declaring all the views name
      let aqlView = `aqlView_${dbCount}`;

      // deleting aqlSoundex analyzer
      deleteAnalyzer(aqlSoundex)

      // // deleting created Views
      // try {
      //   db._dropView(aqlView);
      // } catch (e) {
      //   print(e);
      // }

      // //deleting created collections
      // try {
      //   db._drop("coll");
      // } catch (e) {
      //   print(e);
      // }

      return 0;
    }
  };

}());
