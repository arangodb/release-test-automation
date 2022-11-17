/* global print, semver, progress, createSafe, createCollectionSafe, db */
/*jslint maxlen: 100*/

// const analyzers = require("@arangodb/analyzers");
function createAnalyzer(analyzerName, analyzerCreationQuery){
  // creating analyzer
  let text = createSafe(analyzerName,
                        function () {
                          return analyzerCreationQuery;
                        }, function () {
                          if (analyzers.analyzer(analyzerName) === null) {
                            throw new Error(`609: ${analyzerName} analyzer creation failed!`);
                          }
                        });
}
function getTestData_609(dbCount) {
  return [
    {
      analyzerName: `collationEn_${dbCount}`,
      bindVars: {
        analyzerName: `collationEn_${dbCount}`,
        "@testView": `collationEnView_${dbCount}`
      },
      query: "FOR doc IN @@testView SEARCH ANALYZER(doc.text < TOKENS('c', @analyzerName)[0], @analyzerName) RETURN doc.text",
      analyzerProperties: [
        "collation",
        { locale: "en.utf-8" },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "collation",
      collection: `collationEnCol_${dbCount}`,
      colTestData: [{ text: "a" },{ text: "å" },{ text: "b" },{ text: "z" }],
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
      analyzerName: `collationSv_${dbCount}`,
      bindVars: {
        analyzerName: `collationSv_${dbCount}`,
        "@testView": `collationSvView_${dbCount}`
      },
      query: "FOR doc IN @@testView SEARCH ANALYZER(doc.text < TOKENS('c', @analyzerName)[0], @analyzerName) RETURN doc.text",
      analyzerProperties: [
        "collation",
        { locale: "sv.utf-8" },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "collation",
      collection: `collationSvCol_${dbCount}`,
      colTestData: [{ text: "a" },{ text: "å" },{ text: "b" },{ text: "z" }],
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
      analyzerName: `segmentAll_${dbCount}`,
      bindVars: {
        analyzerName: `segmentAll_${dbCount}`
      },
      query: 'LET str = "Test\twith An_EMAIL-address+123@example.org" RETURN {"all": TOKENS(str, @analyzerName),}',
      analyzerProperties: [
        "segmentation",
        {
          'break': "all"
        }, [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "segmentation",
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
      analyzerName: `segmentAlpha_${dbCount}`,
      bindVars: {
        analyzerName: `segmentAlpha_${dbCount}` 
      },
      query: "LET str = 'Test\twith An_EMAIL-address+123@example.org' RETURN {'alpha': TOKENS(str, @analyzerName),}",
      analyzerProperties: [
        "segmentation",
        {
          'break': "alpha"
        },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "segmentation",
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
      analyzerName: `segmentGraphic_${dbCount}`,
      bindVars: {
        analyzerName: `segmentGraphic_${dbCount}`
      },
      query: "LET str = 'Test\twith An_EMAIL-address+123@example.org' RETURN {'alpha': TOKENS(str, @analyzerName),}",
      analyzerProperties: [
        "segmentation",
        {
          'break': "graphic"
        },
        [
          "frequency",
          "norm",
          "position"
        ]
      ],
      analyzerType: "segmentation",
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
}

(function () {
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
      getTestData_609(dbCount).forEach((test) => {
        let q = analyzers.save(test.analyzerName,
                               ...test.analyzerProperties
                              );
        if (test.hasOwnProperty("collection")) {
          progress(`609: creating ${test.collection} `);
          createCollectionSafe(test.collection, 2, 1).insert(test.colTestData);
          progress(`609: creating ${test['@testView']} `);
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
        progress(`609: creating ${test.analyzerName}`);
        createAnalyzer(test.analyzerName, q);
      });

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
          throw new Error(`609: ${analyzer_name} analyzer's type missmatched! ${JSON.stringify(obj1)} != ${JSON.stringify(obj2)}`);
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

        if (analyzers.analyzer(test.analyzerName) === null) {
          throw new Error(`609: ${test.analyzerName} analyzer creation failed!`);
        }

        progress(`609: ${test.analyzerName} checking analyzer's name`);
        let testName = analyzers.analyzer(test.analyzerName).name();
        let expectedName = `_system::${test.analyzerName}`;
        if (testName !== expectedName) {
          throw new Error(`609: ${test.analyzerName} analyzer not found`);
        }

        progress(`609: ${test.analyzerName} checking analyzer's type`);
        let testType = analyzers.analyzer(test.analyzerName).type();
        if (testType !== test.analyzerType){
          throw new Error(`609: ${test.analyzerName} analyzer type missmatched!`);
        }

        progress(`609: ${test.analyzerName} checking analyzer's properties`);
        let testProperties = analyzers.analyzer(test.analyzerName).properties();
        checkProperties(test.analyzerName, testProperties, test.properties);

        progress(`609: ${test.analyzerName} checking analyzer's query results`);
        arraysEqual(test.expectedResult, queryResult);

        progress(`609: ${test.analyzerName} done`);
      }

      getTestData_609(dbCount).forEach(test => {
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
            throw new Error(`609: ${analyzerName} analyzer isn't deleted yet!`);
          }
        } catch (e) {
          print(e);
        }
        progress(`609: deleted ${analyzerName}`);
      }
      getTestData_609(dbCount).forEach(test => {
        if (test.hasOwnProperty("collection")) {
          progress(`609: deleting view ${test.bindVars["@testView"]} `);
          try {
            db._dropView(test.bindVars["@testView"]);
          } catch (ex) {
            print(ex);
          }
          progress(`609: deleting collection ${test.collection} `);
          try {
            db._drop(test.collection);
          } catch (ex) {
            print(ex);
          }
        }
        progress(`609: deleting Analyzer ${test.analyzerName}`);
        deleteAnalyzer(test.analyzerName);
      });
      return 0;
    }
  };

}());
