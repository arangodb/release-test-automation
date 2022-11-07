/* global print, semver, progress, createSafe, createCollectionSafe, db */
/*jslint maxlen: 130 */

function getTestData(dbcount) {
  return [
    {
      bindVars: {
        analyzerName: `collationEn_${dbCount}`,
        '@collationView': `collationEnView_${dbCount}`,
      },
      query: 'FOR doc IN @@collationView SEARCH ANALYZER(doc.text < TOKENS("c", @analyzerName)[0], @analyzerName) RETURN doc.text',
      collationType: "collation",
      properties: {
        "locale" : "en"
      },
      expectedResult: [
        [
          "a",
          "å",
          "b"
        ]
      ]
    },
    {
      bindVars: {
        analyzerName: `collationSv_${dbCount}`,
        '@collationView': `collationSvView_${dbCount}`,
      },
      query: 'FOR doc IN @@collationView SEARCH ANALYZER(doc.text < TOKENS("c", @analyzerName)[0], @analyzerName) RETURN doc.text',
      collationType: "collation",
      properties: {
        "locale" : "sv"
      },
      expectedResult: [
        [
          "a",
          "å",
          "b"
        ]
      ]
    },
    {
      bindVars: {
        analyzerName: `segmentAll_${dbCount}`
      },
      query: 'LET str = "Test\twith An_EMAIL-address+123@example.org" RETURN {"all": TOKENS(str, @analyzerName),}',
      collationType: "segmentation",
      properties: {
        "case" : "lower",
        "break" : "all"
      },
      expectedResult: [
        {
          "all" : [
            "test",
            "\t",
            "with",
            " ",
            "an_email",
            "-",
            "address",
            "+",
            "123",
            "@",
            "example.org"
          ]
        }
      ]
    },
    {
      bindVars: {
        analyzerName: `segmentAlpha_${dbCount}` 
      },
      query: "LET str = 'Test\twith An_EMAIL-address+123@example.org' RETURN {'alpha': TOKENS(str, @analyzerName),}",
      collationType: "segmentation",
      properties: {
        "case" : "lower",
        "break" : "alpha"
      },
      expectedResult: [
        {
          "alpha" : [
            "test",
            "with",
            "an_email",
            "address",
            "123",
            "example.org"
          ]
        }
      ]
    },
    {
      bindVars: {
        analyzerName: `segmentGraphic_${dbCount}`
      },
      query: "LET str = 'Test\twith An_EMAIL-address+123@example.org' RETURN {'alpha': TOKENS(str, @analyzerName),}",
      collationType: "segmentation",
      properties: {
        "case" : "lower",
        "break" : "graphic"
      },
      expectedResult: [
        {
          "graphic" : [
            "test",
            "with",
            "an_email",
            "-",
            "address",
            "+",
            "123",
            "@",
            "example.org"
          ]
        }
      ]
    },
  ];
};
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

      print(`609: making per database data ${dbCount}`);
      function createAnalyzer(analyzerName, analyzerCreationQuery){
        // creating analyzer
        let text = createSafe(analyzerName,
                              function () {
                                return analyzerCreationQuery;
                              }, function () {
                                if (a.analyzer(analyzerName) === null) {
                                  throw new Error(`609: ${analyzerName} analyzer creation failed!`);
                                }
                              });
      }

      //collationEn analyzer properties
      //collationEn Analyzer for a phonetically similar term search
      let collationEn = `collationEn_${dbCount}`;
      let collationEnView = `collationEnView_${dbCount}`;
      let collationEnCol = `collationEnCol_${dbCount}`;
      let CollationEnQuery = a.save(`${collationEn}`, "collation", { locale: "en.utf-8" }, ["frequency", "norm", "position"]);
      let enCol = createCollectionSafe(collationEnCol, 2, 1);
      enCol.insert([{ text: "a" },{ text: "å" },{ text: "b" },{ text: "z" },]);
      db._createView(`${collationEnView}`, "arangosearch",{ links: { [collationEnCol]: { analyzers: [collationEn], includeAllFields: true }}});

      //collationSv_ analyzer properties
      //collationSv_ Analyzer for a phonetically similar term search
      let collationSv = `collationSv_${dbCount}`;
      let collationSvView = `collationSvView_${dbCount}`;
      let collationSvCol = `collationSvCol_${dbCount}`;

      let CollationSvQuery = a.save(`${collationSv}`, "collation", { locale: "sv.utf-8" }, ["frequency", "norm", "position"]);
      let svCol = createCollectionSafe(collationSvCol, 2, 1); 
      svCol.insert([{ text: "a" },{ text: "å" },{ text: "b" },{ text: "z" },]);
      db._createView(`${collationSvView}`, "arangosearch",{ links: { [collationSvCol]: { analyzers: [collationSv], includeAllFields: true }}});

      //segmentAll analyzer properties
      //segmentAll Analyzer for a phonetically similar term search
      let segmentAll = `segmentAll_${dbCount}`;
      var all = a.save(`${segmentAll}`, "segmentation", { break: "all" }, ["frequency", "norm", "position"]);
      let segmentAllQuery = all;

      //segmentAlpha analyzer properties
      //segmentAlpha Analyzer for a phonetically similar term search
      let segmentAlpha = `segmentAlpha_${dbCount}`;
      var alpha = a.save(`${segmentAlpha}`, "segmentation", { break: "alpha" }, ["frequency", "norm", "position"]);
      let segmentAlphaQuery = alpha;

      //segmentAlpha analyzer properties
      //segmentAlpha Analyzer for a phonetically similar term search
      let segmentGraphic = `segmentGraphic_${dbCount}`;
      var graphic = a.save(`${segmentGraphic}`, "segmentation", { break: "graphic" }, ["frequency", "norm", "position"]);
      let segmentGraphicQuery = graphic;

      //creating collationEn  analyzer
      createAnalyzer(collationEn, CollationEnQuery);
      //creating collationSv  analyzer
      createAnalyzer(collationSv, CollationSvQuery);
      //creating segmentAll  analyzer
      createAnalyzer(segmentAll, segmentAllQuery);
      //creating segmentAlpha  analyzer
      createAnalyzer(segmentAlpha, segmentAlphaQuery);
      //creating segmentGraphic  analyzer
      createAnalyzer(segmentGraphic, segmentGraphicQuery);

      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      print(`609: checking data ${dbCount}`);
      progress(`609: checking data with ${dbCount}`);

      //This function will check any analyzer's properties
      function checkProperties(analyzer_name, obj1, obj2) {
        const obj1Length = Object.keys(obj1).length;
        const obj2Length = Object.keys(obj2).length;

        if (obj1Length === obj2Length) {
          return Object.keys(obj1).every(
            (key) => obj2.hasOwnProperty(key)
              && obj2[key] === obj1[key]);
        } else {
          throw new Error(`609: ${analyzer_name} analyzer's type missmatched!`);
        }
      };

      //This function will check any analyzer's equality with expected server response
      function arraysEqual(a, b) {
        if ((a === b) && (a === null || b === null) && (a.length !== b.length)){
          throw new Error("609: Didn't get the expected response from the server!");
        }
      }

      // this function will check everything regarding given analyzer
      function checkAnalyzer(test){
        let queryResult = db._query(test);

        if (a.analyzer(test.bindVars.analyzerName) === null) {
          throw new Error(`609: ${test.bindVars.analyzerName} analyzer creation failed!`);
        }

        progress(`609: ${test.bindVars.analyzerName} checking analyzer's name`);
        let testName = a.analyzer(test.bindVars.analyzerName).name();
        let expectedName = `_system::${test.bindVars.analyzerName}`;
        if (testName !== expectedName) {
          throw new Error(`609: ${test.bindVars.analyzerName} analyzer not found`);
        }

        progress(`609: ${test.bindVars.analyzerName} checking analyzer's type`);
        let testType = a.analyzer(test.bindVars.analyzerName).type();
        if (testType !== test.collationType){
          throw new Error(`609: ${test.bindVars.analyzerName} analyzer type missmatched!`);
        }

        progress(`609: ${test.bindVars.analyzerName} checking analyzer's properties`);
        let testProperties = a.analyzer(test.bindVars.analyzerName).properties();
        checkProperties(test.bindVars.analyzerName, testProperties, test.properties);

        progress(`609: ${test.bindVars.analyzerName} checking analyzer's query results`);
        arraysEqual(test.expectedResult, queryResult);

        progress(`609: ${test.bindVars.analyzerName} done`);
      }

      getTestData(dbCount).forEach(test => {
        checkAnalyzer(test)
      });
      return 0;
    },
    clearDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      print(`609: checking data ${dbCount}`);
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
            throw new Error(`609: ${analyzerName} analyzer isn't deleted yet!`);
          }
        } catch (e) {
          print(e);
        }
        progress();
      }

      // declaring all the analyzer's name
      let collationEn = `collationEn_${dbCount}`;
      let collationSv = `collationSv_${dbCount}`;
      let segmentAll = `segmentAll_${dbCount}`;
      let segmentAlpha = `segmentAlpha_${dbCount}`;
      let segmentGraphic = `segmentGraphic_${dbCount}`;

      // declaring all the views name
      let collationEnView = `collationEnView_${dbCount}`;
      let collationSvView = `collationSvView_${dbCount}`;
  

      // deleting created Views
      try {
        db._dropView(collationEnView);
        db._dropView(collationSvView);
      } catch (e) {
        print(e);
      }

      //deleting created collections
      let collationEnCol = `collationEnCol_${dbCount}`;
      let collationSvCol = `collationSvCol_${dbCount}`;
      try {
        db._drop(collationEnCol);
        db._drop(collationSvCol);
      } catch (e) {
        print(e);
      }

      // deleting collationEn analyzer
      deleteAnalyzer(collationEn);
      // deleting collationSv analyzer
      deleteAnalyzer(collationSv);
      // deleting segmentAll analyzer
      deleteAnalyzer(segmentAll);
      // deleting segmentAlpha analyzer
      deleteAnalyzer(segmentAlpha);
      // deleting segmentGraphic analyzer
      deleteAnalyzer(segmentGraphic);

      return 0;
    }
  };

}());
