/* global print, semver, progress, createSafe, createCollectionSafe, db, analyzers, fs, PWD, createAnalyzerSet, checkAnalyzerSet, deleteAnalyzerSet */
/*jslint maxlen: 100*/

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
        createAnalyzerSet('609', test);
      });

      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      print(`609: checking data ${dbCount}`);
      progress(`609: checking data with ${dbCount}`);

      getTestData_609(dbCount).forEach(test => {
        checkAnalyzerSet('609', test);
      });
      return 0;
    },
    clearDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      print(`609: checking data ${dbCount}`);
      // deleting analyzer
      getTestData_609(dbCount).forEach(test => {
        deleteAnalyzerSet('609', test);
      });
      return 0;
    }
  };

}());
