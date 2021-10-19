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
if (wiki == null || wiki == undefined) {
  db._create("wikipedia");
}

analyzers.save(
  "tokenizer", "text",
  { locale: "en", stemming:false, accent:true, case:"none" });
analyzers.save(
  "unigram", "ngram",
  { min: 1, max: 1, preserveOriginal:false, streamType:"utf8" },
  ["frequency", "position", "norm"]);
analyzers.save(
  "bigram", "ngram",
  { min: 2, max: 2, preserveOriginal:false, streamType:"utf8" },
  ["frequency", "position", "norm"]);
analyzers.save(
  "bigramWithoutPosition", "ngram",
  { min: 1, max: 1, preserveOriginal:false, streamType:"utf8" },
  ["frequency", "norm"]);
analyzers.save(
  "trigram", "ngram",
  { min: 3, max: 3, preserveOriginal:false, streamType:"utf8" },
  ["frequency", "position", "norm"]);

db._createView(
  "v_wiki_ngram", "arangosearch",
  {
    links : {
      wikipedia : {
        includeAllFields: true,
        fields: { 
          title: { analyzers: ["unigram", "bigram", "trigram", "identity"] },
          body: { analyzers: ["unigram", "bigram", "trigram", "tokenizer" ] }
        }
  } } });
