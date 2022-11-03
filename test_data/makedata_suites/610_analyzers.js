/* global print, semver, progress, createSafe,createCollectionSafe, db, PWD*/
/*jslint maxlen: 130 */

(function () {
  const a = require("@arangodb/analyzers");
  const fs = require('fs')
  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      let currentVersionSemver = semver.parse(semver.coerce(currentVersion));
      let oldVersionSemver = semver.parse(semver.coerce(oldVersion));
      return semver.gte(oldVersionSemver, "3.10.0") && enterprise;
    },

    makeDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      // documentation link: https://www.arangodb.com/docs/3.10/analyzers.html

      print(`610: making per database data ${dbCount}`);
      function createAnalyzer(analyzerName, analyzerCreationQuery){
        // creating analyzer
        let text = createSafe(analyzerName,
          function () {
            return analyzerCreationQuery
          }, function () {
            if (a.analyzer(analyzerName) === null) {
              throw new Error(`610: ${analyzerName} analyzer creation failed!`);
            }
          });
      }

      //classifierSingle analyzer properties
      //classifierSingle Analyzer which is capable of classifying tokens in the input text.
      let classifierSingle = `classifierSingle_${dbCount}`;
      // let path = `${PWD}model_cooking.bin`;
      let path = `${PWD}/makedata_suites/610_model_cooking.bin`;
      let classifierSingleQuery = a.save(`${classifierSingle}`, "classification", { "model_location": `${path}` }, ["frequency", "norm", "position"]);
      
      //classifierDouble analyzer properties
      //classifierDouble Analyzer which is capable of classifying tokens in the input text.
      let classifierDouble = `classifierDouble_${dbCount}`;
      let classifierDoubleQuery = a.save(`${classifierDouble}`, "classification", { "model_location": `${path}`, "top_k": 2 }, ["frequency", "norm", "position"]);      

      //nearestNeighborsSingle analyzer properties
      //nearestNeighborsSingle Analyzer capable of finding nearest neighbors of tokens in the input.
      let nearestNeighborsSingle = `nearestNeighborsSingle_${dbCount}`;
      let nearestNeighborsSingleQuery = a.save(`${nearestNeighborsSingle}`, "nearest_neighbors", { "model_location": `${path}` }, ["frequency", "norm", "position"]);      

      //nearestNeighborsDouble analyzer properties
      //nearestNeighborsDouble Analyzer capable of finding nearest neighbors of tokens in the input.
      let nearestNeighborsDouble = `nearestNeighborsDouble_${dbCount}`;
      let nearestNeighborsDoubleQuery = a.save(`${nearestNeighborsDouble}`, "nearest_neighbors", { "model_location": `${path}`, "top_k": 2 }, ["frequency", "norm", "position"]);
      
      //myMinHash analyzer properties
      let myMinHash = `myMinHash_${dbCount}`;
      let myMinHashQuery = a.save(`${myMinHash}`, "minhash", {"numHashes": 10, "analyzer": {"type": "delimiter", "properties": {"delimiter": "#", "features": []}}})

      let myMinHashCol = `myMinHashCol_${dbCount}`;
      let minCol = createCollectionSafe(myMinHashCol, 1, 1);
      let path01 = `${PWD}/makedata_suites/610_minhash.json`;
      let minhash_col = fs.read(path01)
      minCol.save(JSON.parse(minhash_col), {silent: true})

      // delimiter
      let myDelimiter = `myDelimiter_${dbCount}`;
      let myDelimiterQuery = a.save(`${myDelimiter}`, "delimiter", {delimiter: "#", "features": []})

      //creating classifierSingle  analyzer
      createAnalyzer(classifierSingle, classifierSingleQuery)
      //creating classifierSingle  analyzer
      createAnalyzer(classifierDouble, classifierDoubleQuery)
      //creating nearestNeighborsSingle  analyzer
      createAnalyzer(nearestNeighborsSingle, nearestNeighborsSingleQuery)
      //creating nearestNeighborsDouble  analyzer
      createAnalyzer(nearestNeighborsDouble, nearestNeighborsDoubleQuery)
      // creating myMinhash analyzer
      createAnalyzer(myMinHash, myMinHashQuery)
      // creating myDelimiter analyzer
      createAnalyzer(myDelimiter, myDelimiterQuery)

      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      print(`610: checking data ${dbCount}`);

      //This function will check any analyzer's properties
      function checkProperties(analyzer_name, obj1, obj2) {
        const obj1Length = Object.keys(obj1).length;
        const obj2Length = Object.keys(obj2).length;

        if (obj1Length === obj2Length) {
            return Object.keys(obj1).every(
                (key) => obj2.hasOwnProperty(key)
                   && obj2[key] === obj1[key]);
        } else {
          throw new Error(`610: ${analyzer_name} analyzer's type missmatched!`);
        }
      };

      //This function will check any analyzer's equality with expected server response
      function arraysEqual(a, b) {
        if ((a === b) && (a === null || b === null) && (a.length !== b.length)){
          throw new Error("610: Didn't get the expected response from the server!");
        }
      }

      // this function will check everything regardin given analyzer
      function checkAnalyzer(analyzerName, expectedType, expectedProperties, expectedResult, queryResult){
        if (a.analyzer(analyzerName) === null) {
          throw new Error(`610: ${analyzerName} analyzer creation failed!`);
        }

        //checking analyzer's name
        let testName = a.analyzer(analyzerName).name();
        let expectedName = `_system::${analyzerName}`;
        if (testName !== expectedName) {
          throw new Error(`610: ${analyzerName} analyzer not found`);
        }
        progress();

        //checking analyzer's type
        let testType = a.analyzer(analyzerName).type();
        if (testType !== expectedType){
          throw new Error(`610: ${analyzerName} analyzer type missmatched!`);
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

      //-------------------------------classifierSingle----------------------------------

      let classifierSingle = `classifierSingle_${dbCount}`;
      let path = `${PWD}/makedata_suites/610_model_cooking.bin`;
      let classifierSingleType = "classification";
      let classifierSingleProperties = { 
        "model_location" : `${path}`, 
        "top_k" : 1, 
        "threshold" : 0 
      };
      let classifierSingleExpectedResult =[
        {
          "all" : [
            "__label__baking"
          ]
        }
      ];

      let classifierSingleQueryResult = db._query(`LET str = "Which baking dish is best to bake a banana bread ?" RETURN {"all": TOKENS(str, "${classifierSingle}")}`);


      checkAnalyzer(classifierSingle, classifierSingleType, classifierSingleProperties, classifierSingleExpectedResult, classifierSingleQueryResult)
      
      //-------------------------------classifierDouble----------------------------------

      let classifierDouble = `classifierDouble_${dbCount}`;
      let classifierDoubleType = "classification";
      let classifierDoubleProperties = { 
        "model_location" : `${path}`, 
        "top_k" : 2, 
        "threshold" : 0 
      };
      let classifierDoubleExpectedResult = [ 
        { 
          "double" : [ 
            "__label__baking", 
            "__label__bread" 
          ] 
        } 
      ];

      let classifierDoubleQueryResult = db._query(`LET str = "Which baking dish is best to bake a banana bread ?" RETURN {"double": TOKENS(str, "${classifierDouble}")}`);

      checkAnalyzer(classifierDouble, classifierDoubleType, classifierDoubleProperties, classifierDoubleExpectedResult, classifierDoubleQueryResult)

      //-------------------------------nearestNeighborsSingle----------------------------------

      let nearestNeighborsSingle = `nearestNeighborsSingle_${dbCount}`;
      let nearestNeighborsSingleType = "nearest_neighbors";
      let nearestNeighborsSingleProperties = { 
        "model_location" : `${path}`, 
        "top_k" : 1 
      };
      let nearestNeighborsSingleExpectedResult =[ 
        { 
          "all" : [ 
            "ingredients", 
            "as" 
          ] 
        } 
      ];

      let nearestNeighborsSingleQueryResult = db._query(`LET str = "salt, oil"RETURN {"all": TOKENS(str, "${nearestNeighborsSingle}")}`);

      checkAnalyzer(nearestNeighborsSingle, nearestNeighborsSingleType, nearestNeighborsSingleProperties, nearestNeighborsSingleExpectedResult, nearestNeighborsSingleQueryResult)

      //-------------------------------nearestNeighborsDouble----------------------------------

      let nearestNeighborsDouble = `nearestNeighborsDouble_${dbCount}`;
      let nearestNeighborsDoubleType = "nearest_neighbors";
      let nearestNeighborsDoubleProperties = { 
        "model_location" : `${path}`, 
        "top_k" : 2 
      };
      let nearestNeighborsDoubleExpectedResult =[ 
        { 
          "double" : [ 
            "ingredients", 
            "whole", 
            "as", 
            "in" 
          ] 
        }  
      ];

      let nearestNeighborsDoubleQueryResult = db._query(`LET str = "salt, oil"RETURN {"double": TOKENS(str, "${nearestNeighborsDouble}")}`);

      checkAnalyzer(nearestNeighborsDouble, nearestNeighborsDoubleType, nearestNeighborsDoubleProperties, nearestNeighborsDoubleExpectedResult, nearestNeighborsDoubleQueryResult)
      

      //-------------------------------myMinHash----------------------------------

      let myMinHash = `myMinHash_${dbCount}`;
      let myMinHashCol = `myMinHashCol_${dbCount}`;
      let myMinHashType = "minhash";
      let myMinHashProperties = { 
        "numHashes" : 10, 
        "analyzer" : { 
          "type" : "delimiter", 
          "properties" : { 
            "delimiter" : "#" 
          } 
        } 
      };
      let myMinHashExpectedResult =[ 
        8000 
      ];

      let myMinHashQueryResult = db._query(`for d in ${myMinHashCol} filter minhash(Tokens(d.dataStr, 'myDelimiter_0'), 10) == d.mh10 collect with count into c return c`)
      
      checkAnalyzer(myMinHash, myMinHashType, myMinHashProperties, myMinHashExpectedResult, myMinHashQueryResult)

      return 0;

    },
    clearDataDB: function (options, isCluster, isEnterprise, dbCount, database) {
      print(`610: checking data ${dbCount}`);
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
            throw new Error(`610: ${analyzerName} analyzer isn't deleted yet!`);
          }
        } catch (e) {
          print(e);
        }
        progress();
      }

      // declaring all the analyzer's name
      let classifierSingle = `classifierSingle_${dbCount}`;
      let classifierDouble = `classifierDouble_${dbCount}`;
      let nearestNeighborsSingle = `nearestNeighborsSingle_${dbCount}`;
      let nearestNeighborsDouble = `nearestNeighborsDouble_${dbCount}`;
      let myMinHash = `myMinHash_${dbCount}`;
      let myDelimiter = `myDelimiter_${dbCount}`;

      // deleting classifierSingle analyzer
      deleteAnalyzer(classifierSingle)
      // deleting classifierDouble analyzer
      deleteAnalyzer(classifierDouble)
      // deleting nearestNeighborsSingle analyzer
      deleteAnalyzer(nearestNeighborsSingle)
      // deleting nearestNeighborsDouble analyzer
      deleteAnalyzer(nearestNeighborsDouble)
      // deleting myMinHashCol analyzer
      deleteAnalyzer(myMinHash)
      // deleting myDelimiter analyzer
      deleteAnalyzer(myDelimiter)

      //deleting created collections
      let myMinHashCol = `myMinHashCol_${dbCount}`;

      try {
        db._drop(myMinHashCol);
      } catch (e) {
        print(e);
      }

      return 0;
    }
  };

}());
