/* global print, semver, progress, createSafe, createCollectionSafe, db */
/*jslint maxlen: 100*/

function createAnalyzer(analyzerName, analyzerCreationQuery){
  // creating analyzer
  let text = createSafe(analyzerName,
                        function () {
                          return analyzerCreationQuery;
                        }, function () {
                          if (analyzers.analyzer(analyzerName) === null) {
                            throw new Error(`610: ${analyzerName} analyzer creation failed!`);
                          }
                        });
}
function getTestData_610(dbCount) {
  return [
    {
      analyzerName: `classifierSingle_${dbCount}`,
      bindVars: {
        analyzerName: `classifierSingle_${dbCount}`
      },
      query: `LET str = "Which baking dish is best to bake a banana bread ?" RETURN {"all": TOKENS(str, @analyzerName)}`,
      analyzerProperties: [
        "classification",
        {
          "model_location": `${PWD}/makedata_suites/610_model_cooking.bin`
        },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "classification",
      properties: {
        "model_location" : `${PWD}/makedata_suites/610_model_cooking.bin`, 
        "top_k" : 1,
        "threshold" : 0
      },
      expectedResult: [
        {
          "all" :
          [
            "__label__baking"
          ]
        }
      ]
    },
    {
      analyzerName: `classifierDouble_${dbCount}`,
      bindVars: {
        analyzerName: `classifierDouble_${dbCount}`
      },
      query: `LET str = "Which baking dish is best to bake a banana bread ?" RETURN {"double": TOKENS(str, @analyzerName)}`,
      analyzerProperties: [
        "classification",
        {
          "model_location": `${PWD}/makedata_suites/610_model_cooking.bin`,
          "top_k": 2 
        },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "classification",
      properties: {
        "model_location" : `${PWD}/makedata_suites/610_model_cooking.bin`, 
        "top_k" : 2,
        "threshold" : 0
      },
      expectedResult: [
        { 
          "double" : [
            "__label__baking",
            "__label__bread"
          ]
        }
      ]
    },
    {
      analyzerName: `nearestNeighborsSingle_${dbCount}`,
      bindVars: {
        analyzerName: `nearestNeighborsSingle_${dbCount}`
      },
      query: `LET str = "salt, oil"RETURN {"all": TOKENS(str, @analyzerName)}`,
      analyzerProperties: [
        "nearest_neighbors",
        {
          "model_location": `${PWD}/makedata_suites/610_model_cooking.bin`
        },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "nearest_neighbors",
      properties: {
        "model_location" : `${PWD}/makedata_suites/610_model_cooking.bin`, 
        "top_k" : 0
      },
      expectedResult: [
        {
          "all" :
          [
            "__label__baking"
          ]
        }
      ]
    },
    {
      analyzerName: `nearestNeighborsDouble_${dbCount}`,
      bindVars: {
        analyzerName: `nearestNeighborsDouble_${dbCount}`
      },
      query: `LET str = "salt, oil"RETURN {"double": TOKENS(str, @analyzerName)}`,
      analyzerProperties: [
        "nearest_neighbors",
        {
          "model_location": `${PWD}/makedata_suites/610_model_cooking.bin`
        },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "nearest_neighbors",
      properties: {
        "model_location" : `${PWD}/makedata_suites/610_model_cooking.bin`, 
        "top_k" : 2
      },
      expectedResult: [
        { 
          "double" :
          [ 
            "ingredients",
            "whole",
            "as",
            "in"
          ]
        }
      ]
    },
    {
      analyzerName: `minhash_${dbCount}`,
      bindVars: {
        analyzerName: `minhash_${dbCount}`
      },
      query: `LET str1 = "The quick brown fox jumps over the lazy dog."LET str2 = "The fox jumps over the crazy dog."RETURN {approx: JACCARD(TOKENS(str1, @analyzerName), TOKENS(str2, @analyzerName))}`,
      analyzerProperties: [
        "minhash",
        {
          analyzer:
          {
            type: "segmentation",
            properties:
            {
              break: "alpha",
              case: "lower"
            }
          },
          numHashes: 5
         },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "minhash",
      properties: {
        "numHashes" : 5,
        "analyzer" :
        {
          "type" : "segmentation",
          "properties" :
          {
            "case" : "lower",
            "break" : "alpha"
          }
        }
      },
      expectedResult: [
        {
          "approx" : 0.42857142857142855
        }
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
      return enterprise && semver.gt(oldVersionSemver, "3.10.0");
    },

    makeDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      // documentation link: https://www.arangodb.com/docs/3.10/analyzers.html

      print(`610: making per database data ${dbCount}`);
      getTestData_610(dbCount).forEach((test) => {
        let q = analyzers.save(test.analyzerName,
                               ...test.analyzerProperties
                              );
        if (test.hasOwnProperty("collection")) {
          progress(`610: creating ${test.collection} `);
          createCollectionSafe(test.collection, 2, 1).insert(test.colTestData);
          progress(`610: creating ${test["@testView"]} `);
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
        progress(`610: creating ${test.analyzerName}`);
        createAnalyzer(test.analyzerName, q);
      });
      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      print(`610: checking data ${dbCount}`);
      progress(`610: checking data with ${dbCount}`);

      //This function will check any analyzer's properties
      function checkProperties(analyzer_name, obj1, obj2) {
        const obj1Length = Object.keys(obj1).length;
        const obj2Length = Object.keys(obj2).length;

        if (obj1Length === obj2Length) {
            return Object.keys(obj1).every(
                (key) => obj2.hasOwnProperty(key)
                   && obj2[key] === obj1[key]);
        } else {
          throw new Error(`610: ${analyzer_name} analyzer's type missmatched! ${JSON.stringify(obj1)} != ${JSON.stringify(obj2)}`);
        }
      };

      //This function will check any analyzer's equality with expected server response
      function arraysEqual(a, b) {
        if ((a === b) && (a === null || b === null) && (a.length !== b.length)){
          throw new Error("610: Didn't get the expected response from the server!");
        }
      }

      // this function will check everything regarding given analyzer
      function checkAnalyzer(test){
        let queryResult = db._query(test);

        if (analyzers.analyzer(test.analyzerName) === null) {
          throw new Error(`610: ${test.analyzerName} analyzer creation failed!`);
        }

        progress(`610: ${test.analyzerName} checking analyzer's name`);
        let testName = analyzers.analyzer(test.analyzerName).name();
        let expectedName = `_system::${test.analyzerName}`;
        if (testName !== expectedName) {
          throw new Error(`610: ${test.analyzerName} analyzer not found`);
        }

        progress(`610: ${test.analyzerName} checking analyzer's type`);
        let testType = analyzers.analyzer(test.analyzerName).type();
        if (testType !== test.analyzerType){
          throw new Error(`610: ${test.analyzerName} analyzer type missmatched! ${testType} != ${test.analyzerType}`);
        }

        progress(`610: ${test.analyzerName} checking analyzer's properties`);
        let testProperties = analyzers.analyzer(test.analyzerName).properties();
        checkProperties(test.analyzerName, testProperties, test.properties);

        progress(`610: ${test.analyzerName} checking analyzer's query results`);
        arraysEqual(test.expectedResult, queryResult);

        progress(`610: ${test.analyzerName} done`);
      }

      getTestData_610(dbCount).forEach(test => {
        checkAnalyzer(test);
      });
      return 0;
    },
    clearDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      print(`610: checking data ${dbCount}`);
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
            throw new Error(`610: ${analyzerName} analyzer isn't deleted yet!`);
          }
        } catch (e) {
          print(e);
        }
        progress(`610: deleted ${analyzerName}`);
      }
      getTestData_610(dbCount).forEach(test => {
        if (test.hasOwnProperty('collection')) {
          progress(`610: deleting view ${test.bindVars["@testView"]}`);
          try {
            db._dropView(test.bindVars["@testView"]);
          } catch (ex) {
            print(ex);
          }
          progress(`610: deleting collection ${test.collection} `);
          try {
            db._drop(test.collection);
          } catch (ex) {
            print(ex);
          }
        }
        progress(`610: deleting Analyzer ${test.analyzerName}`);
        deleteAnalyzer(test.analyzerName);
      });
      return 0;
    }
  };

}());
