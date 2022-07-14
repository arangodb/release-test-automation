/* global print, semver, progress, createSafe, db */
/*jslint maxlen: 130 */

(function () {
  const a = require("@arangodb/analyzers");
  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise) {
      let currentVersionSemver = semver.parse(semver.coerce(currentVersion));
      let oldVersionSemver = semver.parse(semver.coerce(oldVersion));
      return semver.gt(oldVersionSemver, "3.8.0");
    },

    makeDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      // documentation link: https://www.arangodb.com/docs/3.8/analyzers.html

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

      //aqlSoundex analyzer properties
      //Soundex Analyzer for a phonetically similar term search
      let aqlSoundex = `aqlSoundex_${dbCount}`;
      let aqlSoundexQuery = a.save(`${aqlSoundex}`, "aql", { queryString: "RETURN SOUNDEX(@param)" },["frequency", "norm", "position"]);

      //aqlConcat analyzer properties
      //Concatenating Analyzer for conditionally adding a custom prefix or suffix:
      let aqlConcat = `aqlConcat_${dbCount}`;
      let aqlConcatQuery = a.save(`${aqlConcat}`, "aql", { queryString: "RETURN LOWER(LEFT(@param, 5)) == 'inter' ? CONCAT(@param, 'ism') : CONCAT('inter', @param)"}, ["frequency", "norm", "position"]);
      
      //aqlFilter analyzer properties
      //Filtering Analyzer that discards unwanted data based on the prefix "ir"
      let aqlFilter = `aqlFilter_${dbCount}`;
      let aqlFilterQuery = a.save(`${aqlFilter}`, "aql", 
      { queryString:"FILTER LOWER(LEFT(@param, 2)) != 'ir' RETURN @param"},
      ["frequency", "norm", "position"]); var coll = db._create("coll");
      var doc1 = db.coll.save({ value: "regular" });
      var doc2 = db.coll.save({ value: "irregular" });
      var view = db._createView("view", "arangosearch", 
      { links: { coll: { fields: { value: { analyzers: [`${aqlFilter}`] }}}}})

      //nGramPipeline analyzer properties
      //Normalize to all uppercase and compute bigrams
      let nGramPipeline = `nGramPipeline_${dbCount}`;
      let nGramPipelineQuery = a.save(`${nGramPipeline}`, "pipeline", { pipeline: [{ type: "norm",
      properties: { locale: "en.utf-8", case: "upper" } },{ type: "ngram", properties: { min: 2,
      max: 2, preserveOriginal: false, streamType: "utf8" } }] }, ["frequency", "norm", "position"]);

      //delimiterPipeline analyzer properties
      //Split at delimiting characters , and ;, then stem the tokens:
      let delimiterPipeline = `delimiterPipeline_${dbCount}`;
      let delimiterPipelineQuery = a.save(`${delimiterPipeline}`, "pipeline",
      { pipeline: [{ type: "delimiter", properties: { delimiter: "," } },
      { type: "delimiter", properties: { delimiter: ";" } },
      { type: "stem", properties: { locale: "en.utf-8" } }] },
      ["frequency", "norm", "position"]);

      //creating aqlSoundex analyzer
      createAnalyzer(aqlSoundex, aqlSoundexQuery)
      //creating aqlConcat analyzer
      createAnalyzer(aqlConcat, aqlConcatQuery)
      //creating aqlFilter analyzer
      createAnalyzer(aqlFilter, aqlFilterQuery)
      //creating nGramPipeline analyzer
      createAnalyzer(nGramPipeline, nGramPipelineQuery)
      //creating nGramPipeline analyzer
      createAnalyzer(delimiterPipeline, delimiterPipelineQuery)

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

      //-------------------------------aqlSoundex----------------------------------

      let aqlSoundex = `aqlSoundex_${dbCount}`;
      let aqlSoundexType = "aql";
      let aqlSoundexProperties = {
        "queryString" : "RETURN SOUNDEX(@param)",
        "collapsePositions" : false,
        "keepNull" : true,
        "batchSize" : 10,
        "memoryLimit" : 1048576,
        "returnType" : "string"
      };
      let aqlSoundexExpectedResult =[
        [
          "A652"
        ]
      ];

      let aqlSoundexQueryReuslt = db._query(`RETURN TOKENS("UPPER lower dïäcríticš", "${aqlSoundex}")`).toArray();

      checkAnalyzer(aqlSoundex, aqlSoundexType, aqlSoundexProperties, aqlSoundexExpectedResult, aqlSoundexQueryReuslt)

      //-------------------------------aqlConcat----------------------------------
      let aqlConcat = `aqlConcat_${dbCount}`;
      let aqlConcatType = "aql";
      let aqlConcatProperties = {
        "queryString" : "RETURN LOWER(LEFT(@param, 5)) == 'inter' ? CONCAT(@param, 'ism') : CONCAT('inter', @param)",
        "collapsePositions" : false,
        "keepNull" : true,
        "batchSize" : 10,
        "memoryLimit" : 1048576,
        "returnType" : "string"
      };
      let aqlConcatExpectedResult =[
        [
          [
            "internationalism"
          ],
          [
            "interstate"
          ]
        ]
      ];

      let aqlConcatQueryReuslt = db._query(`RETURN TOKENS(['international', 'state'], "${aqlConcat}")`);

      checkAnalyzer(aqlConcat, aqlConcatType, aqlConcatProperties, aqlConcatExpectedResult, aqlConcatQueryReuslt)

      //-------------------------------aqlFilter----------------------------------

      let aqlFilter = `aqlFilter_${dbCount}`;
      let aqlFilterType = "aql";
      let aqlFilterProperties = {
        "queryString" : "FILTER LOWER(LEFT(@param, 2)) != 'ir' RETURN @param",
        "collapsePositions" : false,
        "keepNull" : true,
        "batchSize" : 10,
        "memoryLimit" : 1048576,
        "returnType" : "string"
      };
      let aqlFilterExpectedResult =[
        {
          "_key" : "41974",
          "_id" : "coll/41974",
          "_rev" : "_edswByC---",
          "value" : "regular"
        }
      ];

      let aqlFilterQueryReuslt = db._query(`FOR doc IN view SEARCH ANALYZER(doc.value IN ['regular', 'irregular'], '${aqlFilter}') RETURN doc`);
      
      checkAnalyzer(aqlFilter, aqlFilterType, aqlFilterProperties, aqlFilterExpectedResult, aqlFilterQueryReuslt)


      //-------------------------------nGramPipeline----------------------------------

      let nGramPipeline = `nGramPipeline_${dbCount}`;
      let nGramPipelineType = "pipeline";
      let nGramPipelineProperties = {
        "pipeline" : [
          {
            "type" : "norm",
            "properties" : {
              "locale" : "en",
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
              "streamType" : "utf8",
              "startMarker" : "",
              "endMarker" : ""
            }
          }
        ]
      };
      let nGramPipelineExpectedResult =[
        [
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
        ]
      ];

      let nGramPipelineQueryReuslt = db._query(`RETURN TOKENS("Quick brown foX", "${nGramPipeline}")`).toArray();

      checkAnalyzer(nGramPipeline, nGramPipelineType, nGramPipelineProperties, nGramPipelineExpectedResult, nGramPipelineQueryReuslt)


      //-------------------------------delimiterPipeline----------------------------------

      let delimiterPipeline = `delimiterPipeline_${dbCount}`;
      let delimiterPipelineType = "pipeline";
      let delimiterPipelineProperties = {
        "pipeline" : [
          {
            "type" : "delimiter",
            "properties" : {
              "delimiter" : ","
            }
          },
          {
            "type" : "delimiter",
            "properties" : {
              "delimiter" : ";"
            }
          },
          {
            "type" : "stem",
            "properties" : {
              "locale" : "en"
            }
          }
        ]
      };
      let delimiterPipelineExpectedResult =[
        [
          "delimit",
          "stemmabl",
          "word"
        ]
      ];

      let delimiterPipelineQueryReuslt = db._query(`RETURN TOKENS("delimited,stemmable;words", "${delimiterPipeline}")`).toArray();

      checkAnalyzer(delimiterPipeline, delimiterPipelineType, delimiterPipelineProperties, delimiterPipelineExpectedResult, delimiterPipelineQueryReuslt)


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
      let aqlConcat = `aqlConcat_${dbCount}`;
      let aqlFilter = `aqlFilter_${dbCount}`;
      let nGramPipeline = `nGramPipeline_${dbCount}`;
      let delimiterPipeline = `delimiterPipeline_${dbCount}`;
      
      // deleting aqlSoundex analyzer
      deleteAnalyzer(aqlSoundex)
      // deleting aqlConcat analyzer
      deleteAnalyzer(aqlConcat)
      // deleting aqlFilter analyzer
      deleteAnalyzer(aqlFilter)
      // deleting nGramPipeline analyzer
      deleteAnalyzer(nGramPipeline)
      // deleting delimiterPipeline analyzer
      deleteAnalyzer(delimiterPipeline)

      return 0;
    }
  };

}());
