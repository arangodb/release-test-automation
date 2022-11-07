/* global print, semver, progress, createSafe, db */

(function () {
  const a = require("@arangodb/analyzers");
  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      let currentVersionSemver = semver.parse(semver.coerce(currentVersion));
      let oldVersionSemver = semver.parse(semver.coerce(oldVersion));
      return semver.gt(oldVersionSemver, "3.7.0");
    },

    makeDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      // documentation link: https://www.arangodb.com/docs/3.7/analyzers.html

      print(`607: making per database data ${dbCount}`);
      function createAnalyzer(analyzerName, analyzerCreationQuery){
        // creating analyzer
        let text = createSafe(analyzerName,
          function () {
            return analyzerCreationQuery
          }, function () {
            if (a.analyzer(analyzerName) === null) {
              throw new Error(`607: ${analyzerName} analyzer creation failed!`);
            }
          });
      }

      //identity analyzer properties
      let identity = `identity_${dbCount}`;
      let identityQuery = a.save(`${identity}`, "identity");

      //delimiter analyzer properties
      let delimiter = `delimiter_${dbCount}`;
      let delimiterQuery =
      a.save(`${delimiter}`, "delimiter",
      {delimiter: "-"}, ["frequency", "norm", "position"]);

      //stem analyzer properties
      let stem = `stem_${dbCount}`;
      let stemQuery =
      a.save(`${stem}`, "stem", {locale: "en.utf-8"}, ["frequency",
      "norm", "position"]);

      //norm upper analyzer properties
      let normUpper = `normUpper_${dbCount}`;
      let normUpperQuery =
      a.save(`${normUpper}`, "norm", {locale: "en.utf-8", case: "upper"}, ["frequency",
      "norm", "position"]);

      //norm Accent analyzer properties
      let normAccent = `normAccent_${dbCount}`;
      let normAccentQuery =
      a.save(`${normAccent}`, "norm", {locale: "en.utf-8",accent: false}, ["frequency",
      "norm", "position"]);

      //n-gram analyzer properties
      let ngram = `ngram_${dbCount}`;
      let ngramQuery =
      a.save(`${ngram}`, "ngram", {min: 3,max: 3,preserveOriginal: false,streamType: "utf8"},
      ["frequency", "norm", "position"]);

      //n-gram bigram analyzer properties
      let nBigramMarkers = `nBigramMarkers_${dbCount}`;
      let nBigramMarkersQuery =
      a.save(`${nBigramMarkers}`, "ngram", {min: 2, max: 2, preserveOriginal: true, startMarker: "^",
      endMarker: "$", streamType: "utf8"}, ["frequency", "norm", "position"]);

      //text edge n-gram analyzer properties
      let textEdgeNgram = `textEdgeNgram_${dbCount}`;
      let textEdgeNgramQuery =
      a.save(`${textEdgeNgram}`, "text", {edgeNgram: { min: 3, max: 8, preserveOriginal: true },locale: "en.utf-8", 
      case: "lower",accent: false,stemming: false,stopwords: [ "the" ]}, ["frequency","norm","position"])


      //text analyzer properties
      let text = `text_${dbCount}`;
      let textQuery =
      a.save(`${text}`, "text", {locale: "el.utf-8",
      stemming: true,
      case: "lower",
      accent: false,
      stopwords: []
      }, ["frequency", "norm", "position"]);


      //creating identity analyzer
      createAnalyzer(identity, identityQuery)
      //creating delimiter analyzer
      createAnalyzer(delimiter, delimiterQuery)
      //creating stem analyzer
      createAnalyzer(stem, stemQuery)
      //creating normUpper analyzer
      createAnalyzer(normUpper, normUpperQuery)
      //creating normAccent analyzer
      createAnalyzer(normAccent, normAccentQuery)
      //creating ngram analyzer
      createAnalyzer(ngram, ngramQuery)
      //creating ngram analyzer
      createAnalyzer(nBigramMarkers, nBigramMarkersQuery)
      //creating text analyzer
      createAnalyzer(text, textQuery)
      //creating textEdgeNgram analyzer
      createAnalyzer(textEdgeNgram, textEdgeNgramQuery)

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
          throw new Error(`607: ${analyzer_name} analyzer's type missmatched!`);
        }
      };

      //This function will check any analyzer's equality with expected server response
      function arraysEqual(a, b) {
        if ((a === b) && (a === null || b === null) && (a.length !== b.length)){
          throw new Error("607: Didn't get the expected response from the server!");
        }
      }

      // this function will check everything regardin given analyzer
      function checkAnalyzer(analyzerName, expectedType, expectedProperties, expectedResult, queryResult){
        if (a.analyzer(analyzerName) === null) {
          throw new Error(`607: ${analyzerName} analyzer creation failed!`);
        }

        //checking analyzer's name
        let testName = a.analyzer(analyzerName).name();
        let expectedName = `_system::${analyzerName}`;
        if (testName !== expectedName) {
          throw new Error(`607: ${analyzerName} analyzer not found`);
        }
        progress();

        //checking analyzer's type
        let testType = a.analyzer(analyzerName).type();
        if (testType !== expectedType){
          throw new Error(`607: ${analyzerName} analyzer type missmatched!`);
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

      //-------------------------------identity----------------------------------

      let identity = `identity_${dbCount}`;
      let identityType = "identity";
      let identityProperties = {};
      let identityExpectedResult =[
        [
          "UPPER lower dïäcríticš"
        ]
      ];

      let identityQueryReuslt = db._query(`RETURN TOKENS("UPPER lower dïäcríticš", "${identity}")`).toArray();

      checkAnalyzer(identity, identityType, identityProperties, identityExpectedResult, identityQueryReuslt)

      //-------------------------------Delimiter----------------------------------

      let delimiter = `delimiter_${dbCount}`;
      let delimiterType = "delimiter";
      let delimiterProperties = {
        "delimiter" : "-"
      };
      let delimiterExpectedResult =[
        [
          "some",
          "delimited",
          "words"
        ]
      ];

      let delimiterQueryReuslt = db._query(`RETURN TOKENS("some-delimited-words", "${delimiter}")`).toArray();

      checkAnalyzer(delimiter, delimiterType, delimiterProperties, delimiterExpectedResult, delimiterQueryReuslt)

      //-------------------------------stem----------------------------------

      let stem = `stem_${dbCount}`;
      let stemType = "stem";
      let stemProperties = {
        "locale" : "en"
      };
      let stemExpectedResult =[
        [
          "databas"
        ]
      ];

      let stemAnalyzerQueryReuslt = db._query(`RETURN TOKENS("databases", "${stem}")`).toArray();

      checkAnalyzer(stem, stemType, stemProperties, stemExpectedResult, stemAnalyzerQueryReuslt)

      //-------------------------------norm upper----------------------------------

      let normUpper = `normUpper_${dbCount}`;
      let normType = "norm";
      let normProperties = {
        "locale" : "en",
        "case" : "upper",
        "accent" : true
      };
      let normExpectedResult =[
        [
          "UPPER LOWER DÏÄCRÍTICŠ"
        ]
      ];

      let normQueryReuslt = db._query(`RETURN TOKENS("UPPER lower dïäcríticš", "${normUpper}")`).toArray();

      checkAnalyzer(normUpper, normType, normProperties, normExpectedResult, normQueryReuslt)

      //-------------------------------norm Accent----------------------------------

      let normAccent = `normAccent_${dbCount}`;
      let normAccentType = "norm";
      let normAccentProperties = {
        "locale" : "en",
        "case" : "none",
        "accent" : false
      };
      let normAccentExpectedResult =[
        [
          "UPPER lower diacritics"
        ]
      ];

      let normAccentQueryReuslt = db._query(`RETURN TOKENS("UPPER lower dïäcríticš", "${normAccent}")`).toArray();

      checkAnalyzer(normAccent, normAccentType, normAccentProperties, normAccentExpectedResult, normAccentQueryReuslt)

      //-------------------------------ngram----------------------------------

      let ngram = `ngram_${dbCount}`;
      let ngramType = "ngram";
      let ngramProperties = {
        "min" : 3,
        "max" : 3,
        "preserveOriginal" : false,
        "streamType" : "utf8",
        "startMarker" : "",
        "endMarker" : ""
      };
      let ngramExpectedResult =[
        [
          "foo",
          "oob",
          "oba",
          "bar"
        ]
      ];

      let ngramQueryReuslt = db._query(`RETURN TOKENS("foobar", "${ngram}")`).toArray();

      checkAnalyzer(ngram, ngramType, ngramProperties, ngramExpectedResult, ngramQueryReuslt)

      //-------------------------------nBigramMarkers----------------------------------

      let nBigramMarkers = `nBigramMarkers_${dbCount}`;
      let nBigramMarkersType = "ngram";
      let nBigramMarkersProperties = {
        "min" : 2,
        "max" : 2,
        "preserveOriginal" : true,
        "streamType" : "utf8",
        "startMarker" : "^",
        "endMarker" : "$"
      };
      let nBigramMarkersExpectedResult =[
        [
          "^fo",
          "^foobar",
          "foobar$",
          "oo",
          "ob",
          "ba",
          "ar$"
        ]
      ];

      let nBigramMarkersQueryReuslt = db._query(`RETURN TOKENS("foobar", "${nBigramMarkers}")`).toArray();

      checkAnalyzer(nBigramMarkers, nBigramMarkersType, nBigramMarkersProperties, nBigramMarkersExpectedResult, nBigramMarkersQueryReuslt)

      //---------------------------------text-------------------------------------

      let text = `text_${dbCount}`;
      let textType = "text";
      let textProperties = {
        "locale" : "el.utf-8",
        "case" : "lower",
        "stopwords" : [ ],
        "accent" : false,
        "stemming" : true
      };
      let textExpectedResult =[
        [
          "crazy",
          "fast",
          "nosql",
          "database"
        ]
      ];

      let textQueryReuslt = db._query(`RETURN TOKENS("Crazy fast NoSQL-database!", "${text}")`).toArray();

      checkAnalyzer(text, textType, textProperties, textExpectedResult, textExpectedResult)

      //-------------------------------TextedgeNgram----------------------------------

      let textEdgeNgram = `textEdgeNgram_${dbCount}`;
      let textEdgeNgramType = "text";
      let textEdgeNgramProperties = {
        "locale" : "en",
        "case" : "lower",
        "stopwords" : [
          "the"
        ],
        "accent" : false,
        "stemming" : false,
        "edgeNgram" : {
          "min" : 3,
          "max" : 8,
          "preserveOriginal" : true
        }
      };
      let textEdgeNgramExpectedResult =[
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
      ];

      let textEdgeNgramQueryReuslt = db._query(`RETURN TOKENS("The quick brown fox jumps over the dogWithAVeryLongName",
      "${textEdgeNgram}")`).toArray();

      checkAnalyzer(textEdgeNgram, textEdgeNgramType, textEdgeNgramProperties, textEdgeNgramExpectedResult, textEdgeNgramExpectedResult)

      return 0;
    },
    clearDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      print(`607: checking data ${dbCount}`);
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
            throw new Error(`607: ${analyzerName} analyzer isn't deleted yet!`);
          }
        } catch (e) {
          print(e);
        }
        progress();
      }

      // declaring all the analyzer's name
      let identity = `identity_${dbCount}`;
      let delimiter = `delimiter_${dbCount}`;
      let stem = `stem_${dbCount}`;
      let normUpper = `normUpper_${dbCount}`;
      let normAccent = `normAccent_${dbCount}`;
      let ngram = `ngram_${dbCount}`;
      let nBigramMarkers = `nBigramMarkers_${dbCount}`;
      let text = `text_${dbCount}`;
      let textEdgeNgram = `textEdgeNgram_${dbCount}`;

      // deleting delimiter analyzer
      deleteAnalyzer(identity)
      progress();
      deleteAnalyzer(delimiter)
      progress();
      deleteAnalyzer(stem)
      progress();
      deleteAnalyzer(normUpper)
      progress();
      deleteAnalyzer(normAccent)
      progress();
      deleteAnalyzer(nBigramMarkers)
      progress();
      deleteAnalyzer(ngram)
      progress();
      deleteAnalyzer(text)
      progress();
      deleteAnalyzer(textEdgeNgram)
      progress();

      return 0;
    },
  };

}());
