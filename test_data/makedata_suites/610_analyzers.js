/* global print, semver, progress, createSafe, db, PWD*/
/*jslint maxlen: 130 */

(function () {
  const a = require("@arangodb/analyzers");
  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      let currentVersionSemver = semver.parse(semver.coerce(currentVersion));
      let oldVersionSemver = semver.parse(semver.coerce(oldVersion));
      return semver.gte(oldVersionSemver, "3.10.0");
    },

    makeDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      // documentation link: https://www.arangodb.com/docs/3.10/analyzers.html
      // model_cooking.bin : https://fasttext.cc/docs/en/supervised-tutorial.html

      print(`making per database data ${dbCount}`);
      function createAnalyzer(analyzerName, analyzerCreationQuery){
        // creating analyzer
        let text = createSafe(analyzerName,
          function () {
            return analyzerCreationQuery
          }, function () {
            if (a.analyzer(analyzerName) === null) {
              throw new Error(`${analyzerName} analyzer creation failed!`);
            }
          });
      }

      //classifierSingle analyzer properties
      //classifierSingle Analyzer which is capable of classifying tokens in the input text.
      let classifierSingle = `classifierSingle_${dbCount}`;
      let path = `${PWD}model_cooking.bin`;
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

      //creating classifierSingle  analyzer
      createAnalyzer(classifierSingle, classifierSingleQuery)
      //creating classifierSingle  analyzer
      createAnalyzer(classifierDouble, classifierDoubleQuery)
      //creating nearestNeighborsSingle  analyzer
      createAnalyzer(nearestNeighborsSingle, nearestNeighborsSingleQuery)
      //creating nearestNeighborsDouble  analyzer
      createAnalyzer(nearestNeighborsDouble, nearestNeighborsDoubleQuery)

      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      print(`checking data ${dbCount}`);
      progress(`checking data with ${dbCount}`);

      //This function will check any analyzer's properties
      function checkProperties(analyzer_name, obj1, obj2) {
        const obj1Length = Object.keys(obj1).length;
        const obj2Length = Object.keys(obj2).length;

        if (obj1Length === obj2Length) {
            return Object.keys(obj1).every(
                (key) => obj2.hasOwnProperty(key)
                   && obj2[key] === obj1[key]);
        } else {
          throw new Error(`${analyzer_name} analyzer's type missmatched!`);
        }
      };

      //This function will check any analyzer's equality with expected server response
      function arraysEqual(a, b) {
        if ((a === b) && (a === null || b === null) && (a.length !== b.length)){
          throw new Error("Didn't get the expected response from the server!");
        }
      }

      // this function will check everything regardin given analyzer
      function checkAnalyzer(analyzerName, expectedType, expectedProperties, expectedResult, queryResult){
        if (a.analyzer(analyzerName) === null) {
          throw new Error(`${analyzerName} analyzer creation failed!`);
        }

        //checking analyzer's name
        let testName = a.analyzer(analyzerName).name();
        let expectedName = `_system::${analyzerName}`;
        if (testName !== expectedName) {
          throw new Error(`${analyzerName} analyzer not found`);
        }
        progress();

        //checking analyzer's type
        let testType = a.analyzer(analyzerName).type();
        if (testType !== expectedType){
          throw new Error(`${analyzerName} analyzer type missmatched!`);
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
      let path = `${PWD}model_cooking.bin`;
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

      let classifierSingleQueryReuslt = db._query(`LET str = "Which baking dish is best to bake a banana bread ?" RETURN {"all": TOKENS(str, "${classifierSingle}")}`);


      checkAnalyzer(classifierSingle, classifierSingleType, classifierSingleProperties, classifierSingleExpectedResult, classifierSingleQueryReuslt)
      
      //-------------------------------classifierDouble----------------------------------

      let classifierDouble = `classifierDouble_${dbCount}`;
      let classifierDoubleType = "classification";
      let classifierDoubleProperties = { 
        "model_location" : `${path}`, 
        "top_k" : 2, 
        "threshold" : 0 
      };
      let classifierDoubleExpectedResult =[ 
        { 
          "double" : [ 
            "__label__baking", 
            "__label__bread" 
          ] 
        } 
      ];

      let classifierDoubleQueryReuslt = db._query(`LET str = "Which baking dish is best to bake a banana bread ?" RETURN {"double": TOKENS(str, "${classifierDouble}")}`);

      checkAnalyzer(classifierDouble, classifierDoubleType, classifierDoubleProperties, classifierDoubleExpectedResult, classifierDoubleQueryReuslt)

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

      let nearestNeighborsSingleQueryReuslt = db._query(`LET str = "salt, oil"RETURN {"all": TOKENS(str, "${nearestNeighborsSingle}")}`);

      checkAnalyzer(nearestNeighborsSingle, nearestNeighborsSingleType, nearestNeighborsSingleProperties, nearestNeighborsSingleExpectedResult, nearestNeighborsSingleQueryReuslt)

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

      let nearestNeighborsDoubleQueryReuslt = db._query(`LET str = "salt, oil"RETURN {"double": TOKENS(str, "${nearestNeighborsDouble}")}`);

      checkAnalyzer(nearestNeighborsDouble, nearestNeighborsDoubleType, nearestNeighborsDoubleProperties, nearestNeighborsDoubleExpectedResult, nearestNeighborsDoubleQueryReuslt)


      return 0;

    },
    clearDataDB: function (options, isCluster, isEnterprise, dbCount, database) {
      print(`checking data ${dbCount}`);
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
            throw new Error(`${analyzerName} analyzer isn't deleted yet!`);
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

      // deleting classifierSingle analyzer
      deleteAnalyzer(classifierSingle)
      // deleting classifierDouble analyzer
      deleteAnalyzer(classifierDouble)
      // deleting nearestNeighborsSingle analyzer
      deleteAnalyzer(nearestNeighborsSingle)
      // deleting nearestNeighborsDouble analyzer
      deleteAnalyzer(nearestNeighborsDouble)

      return 0;
    }
  };

}());