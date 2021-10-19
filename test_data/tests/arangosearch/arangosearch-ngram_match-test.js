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

const jsunity = require("jsunity");
const errors = require("internal").errors;
const _ = require('lodash');
const {
  assertEqual, assertTrue,
  assertFalse, assertNotEqual,
  assertException, assertNotNull } = jsunity.jsUnity.assertions;
const db = require("@arangodb").db;
const analyzers = require("@arangodb/analyzers");

////////////////////////////////////////////////////////////////////////////////
/// @brief test suite
////////////////////////////////////////////////////////////////////////////////

function ArangoSearch_NGRAM_MATCH() {
  return {
    testNonStringInput: function () {
      try {
        db._query(`
          FOR d IN v_wiki_ngram
            SEARCH NGRAM_MATCH(d.title, null, 1, "bigram")
          SORT d._id
          RETURN d`);
        fail();
      } catch (e) {
        assertEqual(errors.ERROR_BAD_PARAMETER.code, e.errorNum);
      }
    },

    testInvalidAnalyzer: function () {
      try {
        db._query(`
          FOR d IN v_wiki_ngram
            SEARCH NGRAM_MATCH(d.title, "Lord Rings", 1, null)
          SORT d._id
          RETURN d`);
        fail();
      } catch (e) {
        assertEqual(errors.ERROR_BAD_PARAMETER.code, e.errorNum);
      }

      try {
        db._query(`
          FOR d IN v_wiki_ngram
            SEARCH NGRAM_MATCH(d.title, "Lord Rings", 1, "!!invalidAnalyzer@@")
          SORT d._id
          RETURN d`);
        fail();
      } catch (e) {
        assertEqual(errors.ERROR_BAD_PARAMETER.code, e.errorNum);
      }
    },

    testNonStringField: function () {
      let actual = db._query(`
        FOR d IN v_wiki_ngram
          SEARCH NGRAM_MATCH(d.count, "Lord Rings", 1, "bigram")
        SORT d._id
        RETURN d`).toArray();
      assertEqual(actual.length, 0);
    },

    testStringFieldWithoutPositions: function () {
      let actual = db._query(`
        FOR d IN v_wiki_ngram
          SEARCH NGRAM_MATCH(d.title, "Lord Rings", 1, "bigramWithoutPosition")
        SORT d._id
        RETURN d`).toArray();
      assertEqual(actual.length, 0);
    },

    // 0 threshold == match all
    testZeroThreshold: function () {
      let expected = db._query(`
        FOR d IN wikipedia 
        SORT d._key
        RETURN d`).toArray();
      assertNotEqual(expected.length, 0);

      let actual = db._query(`
        FOR d IN v_wiki_ngram
          SEARCH NGRAM_MATCH(d.title, "Lord Rings", 0, "bigram")
        SORT d._id
        RETURN d`).toArray();

      assertEqual(expected.length, actual.length);
      actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i], rhs)));
    },

    testEquality: function () {
      let expected = db._query(`
        FOR d IN wikipedia 
        FILTER [ "Lord", "Rings" ] ALL IN TOKENS(d.title, "tokenizer")
        SORT d._id
        RETURN d`).toArray();
      assertNotEqual(expected.length, 0);

      {
        let actual = db._query(`
          FOR d IN v_wiki_ngram
            SEARCH NGRAM_MATCH(d.title, "Lord Rings", 1, "bigram")
          SORT d._id
          RETURN d`).toArray();

        assertEqual(expected.length, actual.length);
        actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i], rhs)));
      }

      // arguments as bind variables
      {
        let actual = db._query(`
          FOR d IN v_wiki_ngram
            SEARCH NGRAM_MATCH(d.title, @input, @threshold, @analyzer)
          SORT d._id
          RETURN d`, { input : "Lord Rings", analyzer: "bigram", threshold:1}).toArray();

        assertEqual(expected.length, actual.length);
        actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i], rhs)));
      }

      // arguments as references
      {
        let actual = db._query(`
          LET input = NOOPT("Lord Rings")
          LET analyzer = NOOPT("bigram")
          LET threshold = NOOPT(1)
          FOR d IN v_wiki_ngram
            SEARCH NGRAM_MATCH(d.title, input, threshold, analyzer)
          SORT d._id
          RETURN d`).toArray();

        assertEqual(expected.length, actual.length);
        actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i], rhs)));
      }
    }
  };
}

////////////////////////////////////////////////////////////////////////////////
/// @brief executes the test suite
////////////////////////////////////////////////////////////////////////////////

jsunity.run(ArangoSearch_NGRAM_MATCH);
if (false === jsunity.done().status) {
  throw "fail";
}
