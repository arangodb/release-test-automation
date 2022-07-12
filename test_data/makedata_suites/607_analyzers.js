/* global print, semver, progress, createSafe, db */
/*jslint maxlen: 100*/

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

      // creating delimiter analyzer
      progress("create delimiter analyzer");
      let analyzerName01 = `delimiter_${dbCount}`;
      let delimiter = createSafe(analyzerName01,
        function () {
          return a.save(`${analyzerName01}`, "delimiter", {delimiter: "-"}, ["frequency", "norm", "position"]);
        }, function () {
          if (a.analyzer(analyzerName01) === null) {
            throw new Error(`${analyzerName01} analyzer creation failed!`);
          }
        });

      // creating text analyzer
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
            throw new Error(`${analyzerName} analyzer creation failed!`);
          }
        });

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
      }

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

      //-------------------------------Delimiter----------------------------------

      let delimiterAnalyzer = `delimiter_${dbCount}`;
      let delimiterType = "delimiter";
      let delimiterProperties = {
        "delimiter" : "-"
      };
      let delimiterExpectedResult =[
        [
          "some",
          "delimited",
          "words"
        ]
      ];

      let delimiterQueryReuslt = db._query(`RETURN TOKENS("some-delimited-words", "${delimiterAnalyzer}")`).toArray();

      checkAnalyzer(delimiterAnalyzer, delimiterType, delimiterProperties, delimiterExpectedResult, delimiterQueryReuslt)

      //-------------------------------Delimiter----------------------------------


      //---------------------------------text-------------------------------------

      let textAnalyzer = `text_${dbCount}`;
      let textType = "text";
      let textProperties = {
        "locale" : "el.utf-8",
        "case" : "lower",
        "stopwords" : [ ],
        "accent" : false,
        "stemming" : true
      };
      let textExpectedResult =[
        [
          "crazy",
          "fast",
          "nosql",
          "database"
        ]
      ];

      let textQueryReuslt = db._query(`RETURN TOKENS("Crazy fast NoSQL-database!", "${textAnalyzer}")`).toArray();

      //---------------------------------text-------------------------------------

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
      let delimiter = `delimiter_${dbCount}`;
      let text = `text_${dbCount}`;

      // deleting delimiter analyzer
      deleteAnalyzer(delimiter)
      progress();
      deleteAnalyzer(text)
      progress();

      return 0;
    },
  };

}());
