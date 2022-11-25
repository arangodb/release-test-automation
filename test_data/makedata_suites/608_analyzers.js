/* global print, semver, progress, createSafe, createCollectionSafe, db, analyzers, fs, PWD, createAnalyzerSet, checkAnalyzerSet, deleteAnalyzerSet */
/*jslint maxlen: 100*/

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
      analyzerType: "aql",
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
      analyzerType: "aql",
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
        "@testView": `aqlView_${dbCount}`
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
      analyzerType: "aql",
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
                "case": "upper" }
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
      analyzerType: "pipeline",
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
      analyzerType: "pipeline",
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
      analyzerType: "stopwords",
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
      analyzerType: "pipeline",
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
        "@testView": `geoJsonView_${dbCount}`
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
      analyzerType: "geojson",
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
        '@testView': `geoPointView_${dbCount}`
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
      analyzerType: "geopoint",
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
}

(function () {
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
      getTestData_608(dbCount).forEach((test) => {
        createAnalyzerSet('608', test);
      });
      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      print(`608: checking data ${dbCount}`);
      progress(`608: checking data with ${dbCount}`);

      getTestData_608(dbCount).forEach(test => {
        checkAnalyzerSet('608', test);
      });
      return 0;
    },
    clearDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      print(`608: checking data ${dbCount}`);
      // deleting analyzer
      getTestData_608(dbCount).forEach(test => {
        deleteAnalyzerSet('608', test);
      });
      return 0;
    }
  };

}());
