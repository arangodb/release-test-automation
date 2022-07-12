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
      function checkProperties(obj1, obj2, analyzer_name) {
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

      //-------------------------------Delimiter----------------------------------
      
      // checking delimiter analyzer's name
      let analyzerName01 = `delimiter_${dbCount}`;
      if (a.analyzer(analyzerName01) === null) {
        throw new Error(`${analyzerName01} analyzer creation failed!`);
      }

      let testName01 = a.analyzer(analyzerName01).name();
      let expectedName01 = `_system::delimiter_${dbCount}`;
      if (testName01 !== expectedName01) {
        throw new Error(`${analyzerName01} analyzer not found`);
      }
      progress();

      //checking delimiter analyzer's type
      let testType01 = a.analyzer(analyzerName01).type();
      let expectedType01 = "delimiter";
      if (testType01 !== expectedType01){
        throw new Error(`${analyzerName01} analyzer type missmatched!`);
      }
      progress();

      //checking delimiter analyzer's prperties
      let testProperties01 = a.analyzer(analyzerName01).properties();
      let expectedProperties01 = {
        "delimiter" : "-"
      };

      checkProperties(testProperties01, expectedProperties01, analyzerName01);
      progress();

      let myArray01 = [
        [
          "some",
          "delimited",
          "words"
        ]
      ];

      // print(`Create and use a text Analyzer with preserveOriginal disabled:`)
      let textArray01 = db._query(`RETURN TOKENS("some-delimited-words", "${analyzerName01}")`).toArray();
      arraysEqual(myArray01, textArray01);

      //-------------------------------Delimiter----------------------------------


      //-------------------------------text----------------------------------
      // checking text analyzer's name
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

      //checking text analyzer's type
      let testType = a.analyzer(analyzerName).type();
      let expectedType = "text";
      if (testType !== expectedType){
        throw new Error("Analyzer type missmatched!");
      }
      progress();

      //checking text analyzer's properties
      let testProperties = a.analyzer(analyzerName).properties();
      let expectedProperties = {
        "locale" : "el.utf-8",
        "case" : "lower",
        "stopwords" : [ ],
        "accent" : false,
        "stemming" : true
      };

      checkProperties(testProperties, expectedProperties, analyzerName);
      progress();

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
      //-------------------------------text----------------------------------

      return 0;
    },
    clearDataDB: function (options, isCluster, isEnterprise, dbCount, database) {
      print(`checking data ${dbCount}`);
      // declaring all the analyzer's name
      let analyzerName01 = `delimiter_${dbCount}`;
      let analyzerName = `text_${dbCount}`;

      try {
        const array = a.toArray();
        for (let i = 0; i < array.length; i++) {
          const name = array[i];
          if (name === analyzerName01) {
            a.remove(analyzerName01);
          }

          if (name === analyzerName) {
            a.remove(analyzerName);
          }
        }
        // checking created text analyzer is deleted or not
        if (a.analyzer(analyzerName01) != null) {
          throw new Error(`${analyzerName01} analyzer isn't deleted yet!`);
        }
        if (a.analyzer(analyzerName) != null) {
          throw new Error(`${analyzerName} analyzer isn't deleted yet!`);
        }
      } catch (e) {
        print(e);
      }
      progress();

      return 0;
    },
  };

}());
