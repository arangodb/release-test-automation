/* global print, semver, progress, createSafe, createCollectionSafe, db */
/*jslint maxlen: 100*/

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
      let aqlView = `aqlView_${dbCount}`;
      let aqlCol = `aqlCol_${dbCount}`;

      let aqlFilterQuery = a.save(`${aqlFilter}`, "aql",
      { queryString:"FILTER LOWER(LEFT(@param, 2)) != 'ir' RETURN @param"},
      ["frequency", "norm", "position"]); 
      let coll = createCollectionSafe(aqlCol, 1, 1);
      coll.insert({ value: "regular" });
      coll.insert({ value: "irregular" });
      db._createView(`${aqlView}`, "arangosearch",
      { links: { [aqlCol]: { fields: { value: { analyzers: [`${aqlFilter}`] }}}}})

      //nGramPipeline analyzer properties
      //Normalize to all uppercase and compute bigrams
      let nGramPipeline = `nGramPipeline_${dbCount}`;
      let nGramPipelineQuery = a.save(`${nGramPipeline}`, "pipeline", { pipeline: [{ type: "norm",
      properties: { locale: "en.utf-8", case: "upper" } },{ type: "ngram", properties: { min: 2,
      max: 2, preserveOriginal: false, streamType: "utf8" } }] }, ["frequency", "norm", "position"]);

      //delimiterPipeline analyzer properties
      //Split at delimiting characters , and ;, then stem the tokens.
      let delimiterPipeline = `delimiterPipeline_${dbCount}`;
      let delimiterPipelineQuery = a.save(`${delimiterPipeline}`, "pipeline",
      { pipeline: [{ type: "delimiter", properties: { delimiter: "," } },
      { type: "delimiter", properties: { delimiter: ";" } },
      { type: "stem", properties: { locale: "en.utf-8" } }] },
      ["frequency", "norm", "position"]);

      //stopwords analyzer properties
      //Create and use a stopword Analyzer that removes the tokens `and` and `the`
      let stopwords = `stopwords_${dbCount}`;
      let stopwordsQuery = a.save(`${stopwords}`, "stopwords", {stopwords: ["616e64","746865"],
      hex: true}, ["frequency", "norm", "position"]);

      //stopwords analyzer properties
      //Create and use an Analyzer pipeline that normalizes the input (convert to lower-case and base characters)
      //and then discards the stopwords 'and' and 'the'
      let stopwordsPipeline = `stopwordsPipeline_${dbCount}`;
      let stopwordsPipelineQuery = a.save(`${stopwordsPipeline}`, "pipeline",
      { "pipeline": [{ type: "norm", properties: { locale: "en.utf-8", accent: false, case: "lower" } },
      { type: "stopwords", properties: { stopwords: ["and","the"], hex: false } },]},
      ["frequency", "norm", "position"]);

      //geoJson analyzer properties
      //Create a collection with GeoJSON Points stored in an attribute location, a geojson Analyzer with default properties,
      // and a View using the Analyzer. Then query for locations that are within a 3 kilometer radius of a given point and
      // return the matched documents, including the calculated distance in meters. The stored coordinates and the GEO_POINT()
      // arguments are expected in longitude, latitude order:
      let geoJson = `geoJson_${dbCount}`;
      let geoJsonView = `geoJsonView_${dbCount}`;
      let geoJsonQuery = a.save(`${geoJson}`, "geojson", {}, ["frequency", "norm", "position"]);
      let geoJsonCol = `geoJsonCol_${dbCount}`;
      let myCol = createCollectionSafe(geoJsonCol, 2, 1);
      myCol.insert([{ location: { type: "Point", coordinates: [6.937, 50.932] } },
      { location: { type: "Point", coordinates: [6.956, 50.941] } },
      { location: { type: "Point", coordinates: [6.962, 50.932] } },]);
      db._createView(`${geoJsonView}`, "arangosearch", 
      {links: {[geoJsonCol]: {fields: {location: {analyzers: [`${geoJson}`]}}}}});

      //geoPoint analyzer properties
      //An Analyzer capable of breaking up JSON object describing a coordinate into a set
      //of indexable tokens for further usage with ArangoSearch Geo functions.
      let geoPoint = `geoPoint_${dbCount}`;
      let geoPointView = `geoPointView_${dbCount}`;
      let geoPointQuery = a.save(`${geoPoint}`, "geopoint", {}, ["frequency", "norm", "position"]);
      
      let geoPointCol = `geoPointCol_${dbCount}`;
      let myCols = createCollectionSafe(geoPointCol, 3, 2);
      myCols.insert([{ location: [50.932, 6.937] },{ location: [50.941, 6.956] },
      { location: [50.932, 6.962] },]);
      db._createView(`${geoPointView}`, "arangosearch", {links: {[geoPointCol]: {fields: {location: {analyzers: [`${geoPoint}`]}}}}});


      //creating aqlSoundex analyzer
      createAnalyzer(aqlSoundex, aqlSoundexQuery)
      //creating aqlConcat analyzer
      createAnalyzer(aqlConcat, aqlConcatQuery)
      //creating aqlFilter analyzer
      createAnalyzer(aqlFilter, aqlFilterQuery)
      //creating nGramPipeline analyzer
      createAnalyzer(nGramPipeline, nGramPipelineQuery)
      //creating delimiterPipeline analyzer
      createAnalyzer(delimiterPipeline, delimiterPipelineQuery)
      //creating stopwords analyzer
      createAnalyzer(stopwords, stopwordsQuery)
      //creating stopwordsPipeline analyzer
      createAnalyzer(stopwordsPipeline, stopwordsPipelineQuery)
      //creating geoJson analyzer
      createAnalyzer(geoJson, geoJsonQuery)
      //creating geoPoint analyzer
      createAnalyzer(geoPoint, geoPointQuery)


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
      let aqlView = `aqlView_${dbCount}`;
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

      let aqlFilterQueryReuslt = db._query(`FOR doc IN ${aqlView} SEARCH ANALYZER(doc.value IN ['regular', 'irregular'], '${aqlFilter}') RETURN doc`);

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

      //-------------------------------stopwords----------------------------------

      let stopwords = `stopwords_${dbCount}`;
      let stopwordsType = "stopwords";
      let stopwordsProperties = {
        "stopwords" : [
          "616e64",
          "746865"
        ],
        "hex" : true
      };
      let stopwordsExpectedResult =[
        [
          "fox",
          "dog",
          "a",
          "theater"
        ]
      ];

      let stopwordsQueryReuslt = db._query(`RETURN FLATTEN(TOKENS(SPLIT('the fox and the dog and a theater', ' '), "${stopwords}"))`);

      checkAnalyzer(stopwords, stopwordsType, stopwordsProperties, stopwordsExpectedResult, stopwordsQueryReuslt)

      //-------------------------------stopwordsPipeline----------------------------------

      let stopwordsPipeline = `stopwordsPipeline_${dbCount}`;
      let stopwordsPipelineType = "pipeline";
      let stopwordsPipelineProperties = {
        "pipeline" : [
          {
            "type" : "norm",
            "properties" : {
              "locale" : "en",
              "case" : "lower",
              "accent" : false
            }
          },
          {
            "type" : "stopwords",
            "properties" : {
              "stopwords" : [
                "and",
                "the"
              ],
              "hex" : false
            }
          }
        ]
      };
      let stopwordsPipelineExpectedResult =[
        [
          "fox",
          "dog",
          "a",
          "theater"
        ]
      ];

      let stopwordsPipelineQueryReuslt = db._query(`RETURN FLATTEN(TOKENS(SPLIT('The fox AND the dog äñḏ a ţhéäter', ' '), "${stopwordsPipeline}"))`);

      checkAnalyzer(stopwordsPipeline, stopwordsPipelineType, stopwordsPipelineProperties, stopwordsPipelineExpectedResult, stopwordsPipelineQueryReuslt)

      //-------------------------------geoJson----------------------------------

      let geoJson = `geoJson_${dbCount}`;
      let geoJsonView = `geoJsonView_${dbCount}`;
      let geoJsonType = "geojson";
      let geoJsonProperties = {
        "type" : "shape",
        "options" : {
          "maxCells" : 20,
          "minLevel" : 4,
          "maxLevel" : 23
        }
      };
      let geoJsonExpectedResult =[
        {
          "_id" : "geo/603",
          "_key" : "603",
          "_rev" : "_ef_mIDq--_",
          "location" : {
            "type" : "Point",
            "coordinates" : [
              6.937,
              50.932
            ]
          },
          "distance" : 1015.8355739436823
        },
        {
          "_id" : "geo/604",
          "_key" : "604",
          "_rev" : "_ef_mIDq--A",
          "location" : {
            "type" : "Point",
            "coordinates" : [
              6.956,
              50.941
            ]
          },
          "distance" : 1825.1307183571266
        }
      ];

      let geoJsonQueryReuslt = db._query(`LET point = GEO_POINT(6.93, 50.94) FOR doc IN ${geoJsonView} SEARCH ANALYZER(GEO_DISTANCE(doc.location, point) < 2000, "${geoJson}")
      RETURN MERGE(doc, { distance: GEO_DISTANCE(doc.location, point) })`).toArray();

      checkAnalyzer(geoJson, geoJsonType, geoJsonProperties, geoJsonExpectedResult, geoJsonQueryReuslt)

      //-------------------------------geoPoint----------------------------------

      let geoPoint = `geoPoint_${dbCount}`;
      let geoPointView = `geoPointView_${dbCount}`;
      let geoPointType = "geopoint";
      let geoPointProperties = {
        "latitude" : [ ],
        "longitude" : [ ],
        "options" : {
          "maxCells" : 20,
          "minLevel" : 4,
          "maxLevel" : 23
        }
      };
      let geoPointExpectedResult =[
        {
          "_id" : "geo01/2977",
          "_key" : "2977",
          "_rev" : "_efAhNE----",
          "location" : [
            50.932,
            6.937
          ],
          "distance" : 1015.8355739436823
        },
        {
          "_id" : "geo01/2978",
          "_key" : "2978",
          "_rev" : "_efAhNE---_",
          "location" : [
            50.941,
            6.956
          ],
          "distance" : 1825.1307183571266
        }
      ];

      let geoPointQueryReuslt = db._query(`LET point = GEO_POINT(6.93, 50.94) FOR doc IN ${geoPointView} SEARCH ANALYZER(GEO_DISTANCE(doc.location, point) < 2000, "${geoPoint}") RETURN MERGE(doc, { distance: GEO_DISTANCE([doc.location[1], doc.location[0]], point) })`).toArray();


      checkAnalyzer(geoPoint, geoPointType, geoPointProperties, geoPointExpectedResult, geoPointQueryReuslt)


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
      let stopwords = `stopwords_${dbCount}`;
      let stopwordsPipeline = `stopwordsPipeline_${dbCount}`;
      let geoJson = `geoJson_${dbCount}`;
      let geoPoint = `geoPoint_${dbCount}`;

      // declaring all the views name
      let aqlView = `aqlView_${dbCount}`;
      let geoJsonView = `geoJsonView_${dbCount}`;
      let geoPointView = `geoPointView_${dbCount}`;

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
      // deleting stopwords analyzer
      deleteAnalyzer(stopwords)
      // deleting stopwordsPipeline analyzer
      deleteAnalyzer(stopwordsPipeline)
      // deleting geoJson analyzer
      deleteAnalyzer(geoJson)
      // deleting geoPoint analyzer
      deleteAnalyzer(geoPoint)

      // deleting created Views
      try {
        db._dropView(aqlView);
        db._dropView(geoJsonView);
        db._dropView(geoPointView);
      } catch (e) {
        print(e);
      }

      //deleting created collections
      let aqlCol = `aqlCol_${dbCount}`;
      let geoJsonCol = `geoJsonCol_${dbCount}`;
      let geoPointCol = `geoPointCol_${dbCount}`;

      try {
        db._drop(aqlCol);
        db._drop(geoJsonCol);
        db._drop(geoPointCol);
      } catch (e) {
        print(e);
      }

      return 0;
    }
  };

}());
