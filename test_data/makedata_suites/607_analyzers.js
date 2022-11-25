/* global print, semver, progress, createSafe, createCollectionSafe, db, analyzers, fs, PWD, createAnalyzerSet, checkAnalyzerSet, deleteAnalyzerSet */
/*jslint maxlen: 100*/

function getTestData_607(dbCount) {
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
        createAnalyzerSet('607', test);
      });
      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      print(`607: checking data ${dbCount}`);
      progress(`607: checking data with ${dbCount}`);

      getTestData_607(dbCount).forEach(test => {
        checkAnalyzerSet('607', test);
      });
      return 0;
    },
    clearDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      print(`607: checking data ${dbCount}`);
      // deleting analyzer
      getTestData_607(dbCount).forEach(test => {
        deleteAnalyzerSet('607', test);
      });
      return 0;
    }
  };

}());
