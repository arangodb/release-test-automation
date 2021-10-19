/*jshint globalstrict:false, strict:false, maxlen: 500 */
/*global assertUndefined, assertEqual, assertNotEqual, assertTrue, assertFalse, fail*/

////////////////////////////////////////////////////////////////////////////////
/// DISCLAIMER
///
/// Copyright 2020 ArangoDB GmbH, Cologne, Germany
///
/// Licensed under the Apache License, Version 2.0 (the "License");
/// you may not use this file except in compliance with the License.
/// You may obtain a copy of the License at
///
///     http://www.apache.org/licenses/LICENSE-2.0
///
/// Unless required by applicable law or agreed to in writing, software
/// distributed under the License is distributed on an "AS IS" BASIS,
/// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
/// See the License for the specific language governing permissions and
/// limitations under the License.
///
/// Copyright holder is ArangoDB GmbH, Cologne, Germany
///
/// @author Andrey Abramov
////////////////////////////////////////////////////////////////////////////////

const jsunity = require("jsunity");
const {
  assertEqual, assertNotEqual,
  assertTrue, assertFalse,
  assertNull, assertNotNull,
  assertIdentical, assertNotIdentical,
  assertMatch, assertNotMatch,
  assertTypeOf, assertNotTypeOf,
  assertInstanceOf, assertNotInstanceOf,
  assertUndefined, assertNotUndefined,
  assertNan, assertNotNan,
  fail } = jsunity.jsUnity.assertions;
const db = require("@arangodb").db;

function getIndexSize(collectionName, viewName) {
  let collection = db._collection(collectionName);
  assertNotUndefined(collection);
  let view = db._view(viewName);
  assertNotUndefined(view);

  return collection.getIndexes(true, true)
                   .filter(v => v.type === "arangosearch")
                   .filter(v => view._id === v.view.split("/")[1])[0]
                   .figures.indexSize;
}

function ArangoSearch_StoredValuesCompression() {
  return {
    setUpAll: function () {
      db._dropView("v_wiki_stored_compressed");
      db._dropView("v_wiki_stored_raw");
      db._dropView("v_wiki_sorted_compressed");
      db._dropView("v_wiki_sorted_raw");
    },

    tearDownAll: function() {
      db._dropView("v_wiki_stored_compressed");
      db._dropView("v_wiki_stored_raw");
      db._dropView("v_wiki_sorted_compressed");
      db._dropView("v_wiki_sorted_raw");
    },

    testCheckStoredValuesCompression: function() {
      db._createView(
        "v_wiki_stored_compressed",
        "arangosearch",
        {
          storedValues: [ { fields: [ "body", "title" ], compression:"lz4" } ],
          links : { wikipedia : { includeAllFields:true } },
          cleanupIntervalStep:0,
          consolidationIntervalMsec:0
        });
      let compressedSize = getIndexSize("wikipedia", "v_wiki_stored_compressed");
      db._dropView("v_wiki_stored_compressed");

      db._createView(
        "v_wiki_stored_raw",
        "arangosearch",
        {
          storedValues: [ { fields: [ "body", "title" ], compression:"none" } ],
          links : { wikipedia : { includeAllFields:true } },
          cleanupIntervalStep:0,
          consolidationIntervalMsec:0
        });
      let rawSize = getIndexSize("wikipedia", "v_wiki_stored_raw");
      db._dropView("v_wiki_stored_raw");

      print("Compressed=" + compressedSize + " Raw=" + rawSize + " Ratio=" + compressedSize / rawSize);
      assertTrue(compressedSize < rawSize);
    },

    testCheckPrimarySortCompression: function() {
      db._createView(
        "v_wiki_sorted_compressed",
        "arangosearch",
        {
          primarySort: [ { field:"body", asc:true }, { field:"title", asc:true } ],
          primarySortCompression: "lz4",
          links : { wikipedia : { includeAllFields:true } },
          cleanupIntervalStep:0,
          consolidationIntervalMsec:0
        });
      let compressedSize = getIndexSize("wikipedia", "v_wiki_sorted_compressed");
      db._dropView("v_wiki_sorted_compressed");

      db._createView(
        "v_wiki_sorted_raw",
        "arangosearch",
        {
          primarySort: [ { field:"body", asc:true }, { field:"title", asc:true } ],
          primarySortCompression: "none",
          links : { wikipedia : { includeAllFields:true } },
          cleanupIntervalStep:0,
          consolidationIntervalMsec:0
        });
      let rawSize = getIndexSize("wikipedia", "v_wiki_sorted_raw");
      db._dropView("v_wiki_sorted_raw");

      print("Compressed=" + compressedSize + " Raw=" + rawSize + " Ratio=" + compressedSize / rawSize);
      assertTrue(compressedSize < rawSize);
    },
  }
}

////////////////////////////////////////////////////////////////////////////////
/// @brief executes the test suite
////////////////////////////////////////////////////////////////////////////////

jsunity.run(ArangoSearch_StoredValuesCompression);
if (false === jsunity.done().status) {
  throw "fail";
}
