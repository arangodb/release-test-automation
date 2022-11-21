/* global print, semver, progress, createSafe, createCollectionSafe, db, analyzers, fs, PWD, createAnalyzerSet, checkAnalyzerSet, deleteAnalyzerSet */
/*jslint maxlen: 100*/

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
        createAnalyzerSet('610', test);
      });
      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      print(`610: checking data ${dbCount}`);
      progress(`610: checking data with ${dbCount}`);

      getTestData_610(dbCount).forEach(test => {
        checkAnalyzerSet('610', test);
      });
      return 0;
    },
    clearDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      print(`610: checking data ${dbCount}`);
      getTestData_610(dbCount).forEach(test => {
        deleteAnalyzerSet('610', test);
      });
      return 0;
    }
  };

}());
