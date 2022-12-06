/* global print, semver, progress, createSafe, createCollectionSafe, db, analyzers */
/*jslint maxlen: 100*/

const analyzers = require("@arangodb/analyzers");
function createAnalyzer(testgroup, analyzerName, analyzerCreationQuery){
  // creating analyzer
  let text = createSafe(analyzerName,
                        function () {
                          return analyzerCreationQuery;
                        }, function () {
                          if (analyzers.analyzer(analyzerName) === null) {
                            throw new Error(`${testgroup}: ${analyzerName} analyzer creation failed!`);
                          }
                        });
}


function createAnalyzerSet(testgroup, test) {
  let q = analyzers.save(test.analyzerName,
                         ...test.analyzerProperties
                        );
  if (test.hasOwnProperty('collection')) {
    progress(`${testgroup}: creating ${test.collection} `);
    createCollectionSafe(test.collection, 2, 1).insert(test.colTestData);
    progress(`${testgroup}: creating ${test["@testView"]} `);
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
  progress(`${testgroup}: creating ${test.analyzerName}`);
  createAnalyzer(test.analyzerName, q);
}

//This function will check any analyzer's properties
function checkProperties(testgroup, analyzer_name, obj1, obj2) {
  const obj1Length = Object.keys(obj1).length;
  const obj2Length = Object.keys(obj2).length;
  
  if (obj1Length === obj2Length) {
    return Object.keys(obj1).every(
      (key) => obj2.hasOwnProperty(key)
        && obj2[key] === obj1[key]);
  } else {
    throw new Error(`${testgroup}: ${analyzer_name} analyzer's type missmatched! ${JSON.stringify(obj1)} != ${JSON.stringify(obj2)}`);
  }
};

      //This function will check any analyzer's equality with expected server response
function arraysEqual(testgroup, a, b) {
  if ((a === b) && (a === null || b === null) && (a.length !== b.length)){
    throw new Error("${testgroup}: Didn't get the expected response from the server!");
  }
}

// this function will check everything regarding given analyzer
function checkAnalyzerSet(testgroup, test){
  progress(`${testgroup}: ${test.analyzerName} running query ${test.query}`);
  let queryResult = db._query(test);

  if (analyzers.analyzer(test.analyzerName) === null) {
    throw new Error(`${testgroup}: ${test.analyzerName} analyzer creation failed!`);
  }

  progress(`${testgroup}: ${test.analyzerName} checking analyzer's name`);
  let testName = analyzers.analyzer(test.analyzerName).name();
  let expectedName = `_system::${test.analyzerName}`;
  if (testName !== expectedName) {
    throw new Error(`${testgroup}: ${test.analyzerName} analyzer not found`);
  }

  progress(`${testgroup}: ${test.analyzerName} checking analyzer's type`);
  let testType = analyzers.analyzer(test.analyzerName).type();
  if (testType !== test.analyzerType){
    throw new Error(`${testgroup}: ${test.analyzerName} analyzer type missmatched! ${testType} != ${test.analyzerType}`);
  }

  progress(`${testgroup}: ${test.analyzerName} checking analyzer's properties`);
  let testProperties = analyzers.analyzer(test.analyzerName).properties();
  checkProperties(testgroup, test.analyzerName, testProperties, test.properties);

  progress(`${testgroup}: ${test.analyzerName} checking analyzer's query results`);
  arraysEqual(test.expectedResult, queryResult);

  progress(`${testgroup}: ${test.analyzerName} done`);
}

function deleteAnalyzer(testgroup, analyzerName){
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
      throw new Error(`${testgroup}: ${analyzerName} analyzer isn't deleted yet!`);
    }
  } catch (e) {
    print(e);
  }
  progress(`${testgroup}: deleted ${analyzerName}`);
}

function deleteAnalyzerSet(testgroup, test) {
  if (test.hasOwnProperty('collection')) {
    progress(`${testgroup}: deleting view ${test.bindVars['@testView']} `);
    try {
      db._dropView(test.bindVars['@testView']);
    } catch (ex) {
      print(ex);
    }
    progress(`${testgroup}: deleting collection ${test.collection} `);
    try {
      db._drop(test.collection);
    } catch (ex) {
      print(ex);
    }
  }
  progress(`${testgroup}: deleting Analyzer ${test.analyzerName}`);
  deleteAnalyzer(testgroup, test.analyzerName);
}


exports.createAnalyzerSet = createAnalyzerSet;
exports.checkAnalyzerSet = checkAnalyzerSet;
exports.deleteAnalyzerSet = deleteAnalyzerSet;
