/* global print, semver, progress, createSafe, createCollectionSafe, db */
/*jslint maxlen: 100*/

function createAnalyzer(analyzerName, analyzerCreationQuery){
  // creating analyzer
  let text = createSafe(analyzerName,
                        function () {
                          return analyzerCreationQuery;
                        }, function () {
                          if (analyzers.analyzer(analyzerName) === null) {
                            throw new Error(`607: ${analyzerName} analyzer creation failed!`);
                          }
                        });
}
function getTestData_607(dbCount) {
  const a = require("@arangodb/analyzers");
  return [
    {
      analyzerName: `identity_${dbCount}`,
      bindVars: {
        analyzerName: `identity_${dbCount}`
      },
      query: "RETURN TOKENS('UPPER lower dïäcríticš', @analyzerName)",
      analyzerProperties: [
        "identity"
      ],
      analyzerType: "identity",
      properties: {
      },
      expectedResult: [
        [
          "UPPER lower dïäcríticš"
        ]
      ]
    },
    {
      analyzerName: `delimiter_${dbCount}`,
      bindVars: {
        analyzerName: `delimiter_${dbCount}`
      },
      query: "RETURN TOKENS('some-delimited-words', @analyzerName)",
      analyzerProperties: [
        "delimiter",
        {
          delimiter: "-"
        },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "delimiter",
      properties: {
        "delimiter" : "-"
      },
      expectedResult: [
        [
          "some",
          "delimited",
          "words"
        ]
      ]
    },
    {
      analyzerName: `stem_${dbCount}`,
      bindVars: {
        analyzerName: `stem_${dbCount}`
      },
      query: "RETURN TOKENS('databases', @analyzerName)",
      analyzerProperties: [
        "stem",
        {
          locale: "en.utf-8"
        },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "stem",
      properties: {
        "locale" : "en"
      },
      expectedResult: [
        [
          "databas"
        ]
      ]
    },
    {
      analyzerName: `normUpper_${dbCount}`,
      bindVars: {
        analyzerName: `normUpper_${dbCount}`
      },
      query: "RETURN TOKENS('UPPER lower dïäcríticš', @analyzerName)",
      analyzerProperties: [
        "norm",
        {
          locale: "en.utf-8",
          case: "upper"
        },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "norm",
      properties: {
        "locale" : "en",
        "case" : "upper",
        "accent" : true
      },
      expectedResult: [
        [
          "UPPER LOWER DÏÄCRÍTICŠ"
        ]
      ]
    },
    {
      analyzerName: `normAccent_${dbCount}`,
      bindVars: {
        analyzerName: `normAccent_${dbCount}`
      },
      query: "RETURN TOKENS('UPPER lower dïäcríticš', @analyzerName)",
      analyzerProperties: [
        "norm",
        {
          locale: "en.utf-8",
          accent: false
        },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "norm",
      properties: {
        "locale" : "en",
        "case" : "none",
        "accent" : false
      },
      expectedResult: [
        [
          "UPPER lower diacritics"
        ]
      ]
    },
    {
      analyzerName: `ngram_${dbCount}`,
      bindVars: {
        analyzerName: `ngram_${dbCount}`
      },
      query: "RETURN TOKENS('foobar', @analyzerName)",
      analyzerProperties: [
        "ngram",
        {
          min: 3,
          max: 3,
          preserveOriginal: false,
          streamType: "utf8"
        },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "ngram",
      properties: {
        "min" : 3,
        "max" : 3,
        "preserveOriginal" : false,
        "streamType" : "utf8",
        "startMarker" : "",
        "endMarker" : ""
      },
      expectedResult: [
        [
          "foo",
          "oob",
          "oba",
          "bar"
        ]
      ]
    },
    {
      analyzerName: `nBigramMarkers_${dbCount}`,
      bindVars: {
        analyzerName: `nBigramMarkers_${dbCount}`
      },
      query: "RETURN TOKENS('foobar', @analyzerName)",
      analyzerProperties: [
        "ngram",
        {
          min: 2,
          max: 2,
          preserveOriginal: true,
          startMarker: "^",
          endMarker: "$",
          streamType: "utf8"
        },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "ngram",
      properties: {
        "min" : 2,
        "max" : 2,
        "preserveOriginal" : true,
        "streamType" : "utf8",
        "startMarker" : "^",
        "endMarker" : "$"
      },
      expectedResult: [
        [
          "^fo",
          "^foobar",
          "foobar$",
          "oo",
          "ob",
          "ba",
          "ar$"
        ]
      ]
    },
    {
      analyzerName: `textEdgeNgram_${dbCount}`,
      bindVars: {
        analyzerName: `textEdgeNgram_${dbCount}`
      },
      query: "RETURN TOKENS('The quick brown fox jumps over the dogWithAVeryLongName', @analyzerName)",
      analyzerProperties: [
        "text",
        {edgeNgram:
          {
            min: 3,
            max: 8,
            preserveOriginal: true
          },
          locale: "en.utf-8", 
          case: "lower",
          accent: false,
          stemming: false,
          stopwords: [ "the" ]
        },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "text",
      properties: {
        "locale" : "en",
        "case" : "lower",
        "stopwords" : 
        [
          "the"
        ],
        "accent" : false,
        "stemming" : false,
        "edgeNgram" : {
          "min" : 3,
          "max" : 8,
          "preserveOriginal" : true
        }
      },
      expectedResult: [
        [
          "qui",
          "quic",
          "quick",
          "bro",
          "brow",
          "brown",
          "fox",
          "jum",
          "jump",
          "jumps",
          "ove",
          "over",
          "dog",
          "dogw",
          "dogwi",
          "dogwit",
          "dogwith",
          "dogwitha",
          "dogwithaverylongname"
        ]
      ]
    },
    {
      analyzerName: `text_${dbCount}`,
      bindVars: {
        analyzerName: `text_${dbCount}`
      },
      query: "RETURN TOKENS('Crazy fast NoSQL-database!', @analyzerName)",
      analyzerProperties: [
        "text",
        {
          locale: "el.utf-8",
          stemming: true,
          case: "lower",
          accent: false,
          stopwords: []
        },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "text",
      properties: {
        "locale" : "el.utf-8",
        "case" : "lower",
        "stopwords" : [ ],
        "accent" : false,
        "stemming" : true
      },
      expectedResult: [
        [
          "crazy",
          "fast",
          "nosql",
          "database"
        ]
      ]
    }
  ];
}

(function () {
  const a = require("@arangodb/analyzers");
  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise) {
      let currentVersionSemver = semver.parse(semver.coerce(currentVersion));
      let oldVersionSemver = semver.parse(semver.coerce(oldVersion));
      return semver.gt(oldVersionSemver, "3.7.0");
    },

    makeDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      // documentation link: https://www.arangodb.com/docs/3.7/analyzers.html

      print(`607: making per database data ${dbCount}`);
      getTestData_607(dbCount).forEach((test) => {
        let q = analyzers.save(test.analyzerName,
                               ...test.analyzerProperties
                              );
        if (test.hasOwnProperty('collection')) {
          progress(`607: creating ${test.collection} `);
          createCollectionSafe(test.collection, 2, 1).insert(test.colTestData);
          progress(`607: creating ${test["@testView"]} `);
          db._createView(test.bindVars["@testView"],
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
        progress(`607: creating ${test.analyzerName}`);
        createAnalyzer(test.analyzerName, q);
      });
      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      print(`607: checking data ${dbCount}`);
      progress(`607: checking data with ${dbCount}`);

      //This function will check any analyzer's properties
      function checkProperties(analyzer_name, obj1, obj2) {
        const obj1Length = Object.keys(obj1).length;
        const obj2Length = Object.keys(obj2).length;

        if (obj1Length === obj2Length) {
            return Object.keys(obj1).every(
                (key) => obj2.hasOwnProperty(key)
                   && obj2[key] === obj1[key]);
        } else {
          throw new Error(`607: ${analyzer_name} analyzer's type missmatched! ${JSON.stringify(obj1)} != ${JSON.stringify(obj2)}`);
        }
      };

      //This function will check any analyzer's equality with expected server response
      function arraysEqual(a, b) {
        if ((a === b) && (a === null || b === null) && (a.length !== b.length)){
          throw new Error("607: Didn't get the expected response from the server!");
        }
      }

      // this function will check everything regarding given analyzer
      function checkAnalyzer(test){
        let queryResult = db._query(test);

        if (analyzers.analyzer(test.analyzerName) === null) {
          throw new Error(`607: ${test.analyzerName} analyzer creation failed!`);
        }

        progress(`607: ${test.analyzerName} checking analyzer's name`);
        let testName = analyzers.analyzer(test.analyzerName).name();
        let expectedName = `_system::${test.analyzerName}`;
        if (testName !== expectedName) {
          throw new Error(`607: ${test.analyzerName} analyzer not found`);
        }

        progress(`607: ${test.analyzerName} checking analyzer's type`);
        let testType = analyzers.analyzer(test.analyzerName).type();
        if (testType !== test.analyzerType){
          throw new Error(`607: ${test.analyzerName} analyzer type missmatched! ${testType} != ${test.analyzerType}`);
        }

        progress(`607: ${test.analyzerName} checking analyzer's properties`);
        let testProperties = analyzers.analyzer(test.analyzerName).properties();
        checkProperties(test.analyzerName, testProperties, test.properties);

        progress(`607: ${test.analyzerName} checking analyzer's query results`);
        arraysEqual(test.expectedResult, queryResult);

        progress(`607: ${test.analyzerName} done`);
      }

      getTestData_607(dbCount).forEach(test => {
        checkAnalyzer(test);
      });
      return 0;
    },
    clearDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      print(`607: checking data ${dbCount}`);
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
            throw new Error(`607: ${analyzerName} analyzer isn't deleted yet!`);
          }
        } catch (e) {
          print(e);
        }
        progress(`607: deleted ${analyzerName}`);
      }
      getTestData_607(dbCount).forEach(test => {
        if (test.hasOwnProperty('collection')) {
          progress(`607: deleting view ${test.bindVars['@testView']} `);
          try {
            db._dropView(test.bindVars['@testView']);
          } catch (ex) {
            print(ex);
          }
          progress(`607: deleting collection ${test.collection} `);
          try {
            db._drop(test.collection);
          } catch (ex) {
            print(ex);
          }
        }
        progress(`607: deleting Analyzer ${test.analyzerName}`);
        deleteAnalyzer(test.analyzerName);
      });
      return 0;
    }
  };

}());
