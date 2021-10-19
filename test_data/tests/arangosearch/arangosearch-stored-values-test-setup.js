/*jshint globalstrict:false, strict:false, maxlen: 500 */

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

const db = require("@arangodb").db;
const analyzers = require("@arangodb/analyzers");

let wiki = db._collection("wikipedia");
if (wiki === null || wiki === undefined) {
  db._create("wikipedia");
}

let links = db._collection("links");
if (links === null || links === undefined) {
  db._createEdgeCollection("links");
}

db._createView(
  "v_wiki_stored", "arangosearch", {
    storedValues: [
      ["created"],
      ["title", "created", "count", "_id"],
      ["invalidField"]
    ],
    links : { wikipedia : { includeAllFields: true } } });

db._createView(
  "v_wiki_sorted", "arangosearch", {
    primarySort: [
      { field: "_key", asc:true },
      { field: "body", asc:true },
      { field: "created", asc:true },
      { field: "title", asc:true },
      { field: "count", asc:true },
      { field: "_id", asc:true },
      { field: "_rev", asc:true },
    ],
    links : { wikipedia : { includeAllFields: true } } });
