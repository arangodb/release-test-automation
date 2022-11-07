/* global print, semver, progress, createSafe, createCollectionSafe, db */
/*jslint maxlen: 100*/

const analyzers = require("@arangodb/analyzers");
function createAnalyzer(analyzerName, analyzerCreationQuery){
  // creating analyzer
  let text = createSafe(analyzerName,
                        function () {
                          return analyzerCreationQuery;
                        }, function () {
                          if (analyzers.analyzer(analyzerName) === null) {
                            throw new Error(`608: ${analyzerName} analyzer creation failed!`);
                          }
                        });
}
function getTestData_608(dbCount) {
  return [
    {
      analyzerName: `aqlSoundex_${dbCount}`,
      bindVars: {
        analyzerName: `aqlSoundex_${dbCount}`
      },
      query: "RETURN TOKENS('UPPER lower dïäcríticš', @analyzerName)",
      analyzerProperties: [
        "aql",
        {
          queryString: "RETURN SOUNDEX(@param)"
        }, [
          "frequency",
          "norm",
          "position"
        ]
      ],
      collationType: "aql",
      properties: {
        "queryString" : "RETURN SOUNDEX(@param)",
        "collapsePositions" : false,
        "keepNull" : true,
        "batchSize" : 10,
        "memoryLimit" : 1048576,
        "returnType" : "string"
      },
      expectedResult: [
        [
          "A652"
        ]
      ]
    },
    {
      analyzerName: `aqlConcat_${dbCount}`,
      bindVars: {
        param: `aqlConcat_${dbCount}`
      },
      query: "RETURN LOWER(LEFT(@param, 5)) == 'inter' ? CONCAT(@param, 'ism') : CONCAT('inter', @param)",
      analyzerProperties: [
        "aql",
        {
          queryString: "RETURN SOUNDEX(@param)"
        }, [
          "frequency",
          "norm",
          "position"
        ]
      ],
      collationType: "aql",
      properties: {
        "queryString" : "RETURN LOWER(LEFT(@param, 5)) == 'inter' ? CONCAT(@param, 'ism') : CONCAT('inter', @param)",
        "collapsePositions" : false,
        "keepNull" : true,
        "batchSize" : 10,
        "memoryLimit" : 1048576,
        "returnType" : "string"
      },
      expectedResult: [
        [
          [
            "internationalism"
          ],
          [
            "interstate"
          ]
        ]
      ]
    },
    {
      analyzerName: `aqlFilter_${dbCount}`,
      bindVars: {
        analyzerName: `aqlFilter_${dbCount}`,
        '@testView': `aqlView_${dbCount}`,
      },
      query: "FOR doc IN @@testView SEARCH ANALYZER(doc.value IN ['regular', 'irregular'], @analyzerName) RETURN doc",
      analyzerProperties: [
        "aql",
        {
          queryString: "RETURN SOUNDEX(@param)"
        }, [
          "frequency",
          "norm",
          "position"
        ]
      ],
      collection: `aqlCol_${dbCount}`,
      colTestData: [
        { value: "regular" },
        { value: "irregular" }],
      collationType: "aql",
      properties: {
        "queryString" : "FILTER LOWER(LEFT(@param, 2)) != 'ir' RETURN @param",
        "collapsePositions" : false,
        "keepNull" : true,
        "batchSize" : 10,
        "memoryLimit" : 1048576,
        "returnType" : "string"
      },
      expectedResult: [
        {
          "_key" : "41974",
          "_id" : "coll/41974",
          "_rev" : "_edswByC---",
          "value" : "regular"
        }
      ]
    },
    {
      analyzerName: `nGramPipeline_${dbCount}`,
      bindVars: {
        analyzerName: `nGramPipeline_${dbCount}`
      },
      query: "RETURN TOKENS('Quick brown foX', @analyzerName)",
      analyzerProperties: [
        "pipeline", {
          pipeline: [
            { type: "norm",
              properties: {
                locale: "en.utf-8",
                'case': "upper" }
            },{
              type: "ngram",
              properties: {
                min: 2,
                max: 2,
                preserveOriginal: false,
                streamType: "utf8"
              }
            }
          ] },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      collationType: "pipeline",
      properties: {
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
      },
      expectedResult: [
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
      ]
    },
    {
      analyzerName: `delimiterPipeline_${dbCount}`,
      bindVars: {
        analyzerName: `delimiterPipeline_${dbCount}`
      },
      query: "RETURN TOKENS('delimited,stemmable;words', @analyzerName)",
      analyzerProperties: [
        "pipeline",
        {
          pipeline: [
            { type: "delimiter", properties: { delimiter: "," } },
            { type: "delimiter", properties: { delimiter: ";" } },
            { type: "stem", properties: { locale: "en.utf-8" } }
          ]
        },
        [
          "frequency", "norm", "position"
        ]
      ],
      collationType: "pipeline",
      properties: {
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
      },
      expectedResult: [
        [
          "delimit",
          "stemmabl",
          "word"
        ]
      ]
    },
    {
      analyzerName: `stopwords_${dbCount}`,
      bindVars: {
        analyzerName: `stopwords_${dbCount}`
      },
      query: "RETURN TOKENS('delimited,stemmable;words', @analyzerName)",
      analyzerProperties: [
        "stopwords",
        {
          stopwords: ["616e64","746865"],
          hex: true
        },
        ["frequency", "norm", "position"]
      ],
      collationType: "stopwords",
      properties: {
        "stopwords" : [
          "616e64",
          "746865"
        ],
        "hex" : true
      },
      expectedResult: [
        [
          "fox",
          "dog",
          "a",
          "theater"
        ]
      ]
    },
    {
      analyzerName: `stopwordsPipeline_${dbCount}`,
      bindVars: {
        analyzerName: `stopwordsPipeline_${dbCount}`
      },
      query: "RETURN FLATTEN(TOKENS(SPLIT('The fox AND the dog äñḏ a ţhéäter', ' '), @analyzerName))",
      analyzerProperties: [
        "pipeline",
        { "pipeline": [
          { type: "norm", properties: { locale: "en.utf-8", accent: false, case: "lower" } },
          { type: "stopwords", properties: { stopwords: ["and","the"], hex: false } }
        ]
        },
        ["frequency", "norm", "position"]
      ],
      collationType: "pipeline",
      properties: {
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
      },
      expectedResult: [
        [
          "fox",
          "dog",
          "a",
          "theater"
        ]
      ]
    },
    {
      analyzerName: `geoJson_${dbCount}`,
      bindVars: {
        analyzerName: `geoJson_${dbCount}`,
        '@testView': `geoJsonView_${dbCount}`,
      },
      query: "LET point = GEO_POINT(6.93, 50.94) FOR doc IN @@testView SEARCH ANALYZER(GEO_DISTANCE(doc.location, point) < 2000, @analyzerName) RETURN MERGE(doc, { distance: GEO_DISTANCE(doc.location, point) })",
      analyzerProperties: [
        "geojson",
        {},
        ["frequency", "norm", "position"]
      ],
      collection: `geoJsonCol_${dbCount}`,
      colTestData: [
        { location: { type: "Point", coordinates: [6.937, 50.932] } },
        { location: { type: "Point", coordinates: [6.956, 50.941] } },
        { location: { type: "Point", coordinates: [6.962, 50.932] } }
      ],
      collationType: "geojson",
      properties: {
        "type" : "shape",
        "options" : {
          "maxCells" : 20,
          "minLevel" : 4,
          "maxLevel" : 23
        }
      },
      expectedResult: [
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
      ]
    },
    {
      analyzerName: `geoPoint_${dbCount}`,
      bindVars: {
        analyzerName: `geoPoint_${dbCount}`,
        '@testView': `geoPointView_${dbCount}`,
      },
      query: "LET point = GEO_POINT(6.93, 50.94) FOR doc IN @@testView SEARCH ANALYZER(GEO_DISTANCE(doc.location, point) < 2000, @analyzerName) RETURN MERGE(doc, { distance: GEO_DISTANCE([doc.location[1], doc.location[0]], point) })",
      analyzerProperties: [
        "geopoint",
        {},
        ["frequency", "norm", "position"]
      ],
      collection: `geoPointCol_${dbCount}`,
      colTestData: [
        { location: [50.932, 6.937] },
        { location: [50.941, 6.956] },
        { location: [50.932, 6.962] },
      ],
      collationType: "geopoint",
      properties: {
        "latitude" : [ ],
        "longitude" : [ ],
        "options" : {
          "maxCells" : 20,
          "minLevel" : 4,
          "maxLevel" : 23
        }
      },
      expectedResult: [
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
      ]
    },
  ];
};

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

      print(`608: making per database data ${dbCount}`);
      getTestData_608(dbCount).forEach(test => {
        let q = analyzers.save(test.analyzerName,
                               ...test.analyzerProperties
                              );
        if (test.hasOwnProperty('collection')) {
          progress(`609: creating ${test.collection} `);
          createCollectionSafe(test.collection, 2, 1).insert(test.colTestData);
          progress(`609: creating ${test['@testView']} `);
          db._createView(test.bindVars['@testView'],
                         "arangosearch", {
                           links: {
                             [test.collection]:
                             {
                               analyzers: [test.analyzerName],
                               includeAllFields: true
                             }
                           }
                         }
                        );
        }
        progress(`609: creating ${test.analyzerName}`);
        createAnalyzer(test.analyzerName, q);
      });
      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      print(`608: checking data ${dbCount}`);
      progress(`608: checking data with ${dbCount}`);

      //This function will check any analyzer's properties
      function checkProperties(analyzer_name, obj1, obj2) {
        const obj1Length = Object.keys(obj1).length;
        const obj2Length = Object.keys(obj2).length;

        if (obj1Length === obj2Length) {
            return Object.keys(obj1).every(
                (key) => obj2.hasOwnProperty(key)
                   && obj2[key] === obj1[key]);
        } else {
          throw new Error(`608: ${analyzer_name} analyzer's type missmatched! ${JSON.stringify(obj1)} != ${JSON.stringify(obj2)}`);
        }
      };

      //This function will check any analyzer's equality with expected server response
      function arraysEqual(a, b) {
        if ((a === b) && (a === null || b === null) && (a.length !== b.length)){
          throw new Error("608: Didn't get the expected response from the server!");
        }
      }

      // this function will check everything regarding given analyzer
      function checkAnalyzer(test){
        let queryResult = db._query(test);

        if (analyzers.analyzer(test.analyzerName) === null) {
          throw new Error(`608: ${test.analyzerName} analyzer creation failed!`);
        }

        progress(`608: ${test.analyzerName} checking analyzer's name`);
        let testName = analyzers.analyzer(test.analyzerName).name();
        let expectedName = `_system::${test.analyzerName}`;
        if (testName !== expectedName) {
          throw new Error(`608: ${test.analyzerName} analyzer not found`);
        }

        progress(`608: ${test.analyzerName} checking analyzer's type`);
        let testType = analyzers.analyzer(test.analyzerName).type();
        if (testType !== test.collationType){
          throw new Error(`608: ${test.analyzerName} analyzer type missmatched! ${testType} != ${test.collationType}`);
        }

        progress(`608: ${test.analyzerName} checking analyzer's properties`);
        let testProperties = analyzers.analyzer(test.analyzerName).properties();
        checkProperties(test.analyzerName, testProperties, test.properties);

        progress(`608: ${test.analyzerName} checking analyzer's query results`);
        arraysEqual(test.expectedResult, queryResult);

        progress(`608: ${test.analyzerName} done`);
      }

      getTestData_608(dbCount).forEach(test => {
        checkAnalyzer(test);
      });
      return 0;
    },
    clearDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      print(`609: checking data ${dbCount}`);
      // deleting analyzer
      function deleteAnalyzer(analyzerName){
        try {
          const array = analyzers.toArray();
          for (let i = 0; i < array.length; i++) {
            const name = array[i];
            if (name === analyzerName) {
              analyzers.remove(analyzerName);
            }
          }
          // checking created text analyzer is deleted or not
          if (analyzers.analyzer(analyzerName) != null) {
            throw new Error(`608: ${analyzerName} analyzer isn't deleted yet!`);
          }
        } catch (e) {
          print(e);
        }
        progress(`608: deleted ${analyzerName}`);
      }
      getTestData_608(dbCount).forEach(test => {
        if (test.hasOwnProperty('collection')) {
          progress(`608: deleting view ${test.bindVars['@testView']} `);
          try {
            db._dropView(test.bindVars['@testView']);
          } catch (ex) {
            print(ex);
          }
          progress(`608: deleting collection ${test.collection} `);
          try {
            db._drop(test.collection);
          } catch (ex) {
            print(ex);
          }
        }
        progress(`608: deleting Analyzer ${test.analyzerName}`);
        deleteAnalyzer(test.analyzerName);
      });
      return 0;
    }
  };

}());
