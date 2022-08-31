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

      let CollationSvQuery = a.save(`${collationSv}`, "collation", { locale: "en.utf-8" }, ["frequency", "norm", "position"]);
      let svCol = createCollectionSafe(collationSvCol, 2, 1); 
      svCol.insert([{ text: "a" },{ text: "å" },{ text: "b" },{ text: "z" },]);
      db._createView(`${collationSvView}`, "arangosearch",{ links: { [collationSvCol]: { analyzers: [collationSv], includeAllFields: true }}});

      //segmentAll analyzer properties
      //segmentAll Analyzer for a phonetically similar term search
      let segmentAll = `segmentAll_${dbCount}`;
      var all = a.save(`${segmentAll}`, "segmentation", { break: "all" }, ["frequency", "norm", "position"]);
      let segmentAllQuery = all

      //segmentAlpha analyzer properties
      //segmentAlpha Analyzer for a phonetically similar term search
      let segmentAlpha = `segmentAlpha_${dbCount}`;
      var alpha = a.save(`${segmentAlpha}`, "segmentation", { break: "alpha" }, ["frequency", "norm", "position"]);
      let segmentAlphaQuery = alpha

      //segmentAlpha analyzer properties
      //segmentAlpha Analyzer for a phonetically similar term search
      let segmentGraphic = `segmentGraphic_${dbCount}`;
      var graphic = a.save(`${segmentGraphic}`, "segmentation", { break: "graphic" }, ["frequency", "norm", "position"]);
      let segmentGraphicQuery = graphic

      //creating collationEn  analyzer
      createAnalyzer(collationEn, CollationEnQuery)
      //creating collationSv  analyzer
      createAnalyzer(collationSv, CollationSvQuery)
      //creating segmentAll  analyzer
      createAnalyzer(segmentAll, segmentAllQuery)
      //creating segmentAlpha  analyzer
      createAnalyzer(segmentAlpha, segmentAlphaQuery)
      //creating segmentGraphic  analyzer
      createAnalyzer(segmentGraphic, segmentGraphicQuery)

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

      // this function will check everything regarding given analyzer
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

      //-------------------------------collationEn----------------------------------

      let collationEn = `collationEn_${dbCount}`;
      let collationEnView = `collationEnView_${dbCount}`;
      let collationEnType = "collation";
      let collationEnProperties = {
        "locale" : "en"
      };
      let collationEnExpectedResult =[
        [
          "a",
          "å",
          "b"
        ]
      ];

      let collationEnQueryReuslt = db._query(`FOR doc IN ${collationEnView} SEARCH ANALYZER(doc.text < TOKENS('c', '${collationEn}')[0], '${collationEn}') RETURN doc.text`);

      checkAnalyzer(collationEn, collationEnType, collationEnProperties, collationEnExpectedResult, collationEnQueryReuslt)

      //-------------------------------collationSv----------------------------------

      let collationSv = `collationSv_${dbCount}`;
      let collationSvView = `collationSvView_${dbCount}`;
      let collationSvType = "collation";
      let collationSvProperties = {
        "locale" : "en"
      };
      let collationSvExpectedResult =[
        [
          "a",
          "b"
        ]
      ];

      let collationSvQueryReuslt = db._query(`FOR doc IN ${collationSvView} SEARCH ANALYZER(doc.text < TOKENS('c', '${collationSv}')[0], '${collationSv}') RETURN doc.text`);

      checkAnalyzer(collationEn, collationSvType, collationSvProperties, collationSvExpectedResult, collationSvQueryReuslt)

      //-------------------------------segmentAll----------------------------------

      let segmentAll = `segmentAll_${dbCount}`;
      let segmentAllType = "segmentation";
      let segmentAllProperties = {
        "case" : "lower",
        "break" : "all"
      };
      let segmentAllExpectedResult =[
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
      ];

      let segmentAllQueryReuslt = db._query(`LET str = 'Test\twith An_EMAIL-address+123@example.org'RETURN {"all": TOKENS(str, '${segmentAll}'),}`);


      checkAnalyzer(segmentAll, segmentAllType, segmentAllProperties, segmentAllQueryReuslt, segmentAllQueryReuslt)


      //-------------------------------segmentAlpha----------------------------------

      let segmentAlpha = `segmentAlpha_${dbCount}`;
      let segmentAlphaType = "segmentation";
      let segmentAlphaProperties = {
        "case" : "lower",
        "break" : "alpha"
      };
      let segmentAlphaExpectedResult =[
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
      ];

      let segmentAlphaQueryReuslt = db._query(`LET str = 'Test\twith An_EMAIL-address+123@example.org'RETURN {"alpha": TOKENS(str, '${segmentAlpha}'),}`);


      checkAnalyzer(segmentAlpha, segmentAlphaType, segmentAlphaProperties, segmentAlphaExpectedResult, segmentAlphaQueryReuslt)

      //-------------------------------segmentGraphic----------------------------------

      let segmentGraphic = `segmentGraphic_${dbCount}`;
      let segmentGraphicType = "segmentation";
      let segmentGraphicProperties = {
        "case" : "lower",
        "break" : "graphic"
      };
      let segmentGraphicExpectedResult =[
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
      ];

      let segmentGraphicQueryReuslt = db._query(`LET str = 'Test\twith An_EMAIL-address+123@example.org'RETURN {"alpha": TOKENS(str, '${segmentGraphic}'),}`);


      checkAnalyzer(segmentGraphic, segmentGraphicType, segmentGraphicProperties, segmentGraphicExpectedResult, segmentGraphicQueryReuslt)

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
      deleteAnalyzer(collationEn)
      // deleting collationSv analyzer
      deleteAnalyzer(collationSv)
      // deleting segmentAll analyzer
      deleteAnalyzer(segmentAll)
      // deleting segmentAlpha analyzer
      deleteAnalyzer(segmentAlpha)
      // deleting segmentGraphic analyzer
      deleteAnalyzer(segmentGraphic)

      return 0;
    }
  };

}());
