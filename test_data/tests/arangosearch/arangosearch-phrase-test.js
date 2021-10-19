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
const errors = require("internal").errors;
const _ = require('lodash');
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
const analyzers = require("@arangodb/analyzers");

function ArangoSearch_PHRASE() {
  return {
    testNonStringInput: function () {
      try {
        db._query(`
          FOR d IN v_wiki_phrase
            SEARCH PHRASE(d.title, null, "text_en")
          SORT d._id
          RETURN d`);
        fail();
      } catch (e) {
        assertEqual(errors.ERROR_BAD_PARAMETER.code, e.errorNum);
      }
    },

    testInvalidOffset: function () {
      try {
        db._query(`
          FOR d IN v_wiki_phrase
            SEARCH PHRASE(d.title, "Lord Of", "The Rings", "tokenizer")
          SORT d._id
          RETURN d`);
        fail();
      } catch (e) {
        assertEqual(errors.ERROR_BAD_PARAMETER.code, e.errorNum);
      }

      try {
        db._query(`
          FOR d IN v_wiki_phrase
            SEARCH PHRASE(d.title, "Lord Of", null, "The Rings", "tokenizer")
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
          FOR d IN v_wiki_phrase
            SEARCH PHRASE(d.title, "Lord Of The Rings", null)
          SORT d._id
          RETURN d`);
        fail();
      } catch (e) {
        assertEqual(errors.ERROR_BAD_PARAMETER.code, e.errorNum);
      }

      try {
        db._query(`
          FOR d IN v_wiki_phrase
            SEARCH PHRASE(d.title, "Lord Of The Rings", "!!invalidAnalyzer@@")
          SORT d._id
          RETURN d`);
        fail();
      } catch (e) {
        assertEqual(errors.ERROR_BAD_PARAMETER.code, e.errorNum);
      }
    },

    testNonStringField: function () {
      let actual = db._query(`
        FOR d IN v_wiki_phrase
          SEARCH PHRASE(d.count, "Lord Of The Rings", "text_en")
        SORT d._id
        RETURN d`).toArray();
      assertEqual(actual.length, 0);
    },

    testStringFieldWithoutPositions: function () {
      let actual = db._query(`
        FOR d IN v_wiki_phrase
          SEARCH PHRASE(d.title, "Lord Of The Rings", "tokenizerWithoutPosition")
        SORT d._id
        RETURN d`).toArray();
      assertEqual(actual.length, 0);
    },

    testExactPhrase: function () {
      let expected = db._query(`
        LET input = "Lord of The Rings"
        LET phrase = TOKENS(input, "tokenizer")
        FOR d IN wikipedia 
          FILTER LENGTH(d.title) >= LENGTH(input)
          LET tokens = TOKENS(d.title, "tokenizer")
          FILTER phrase ALL IN tokens
          FILTER LENGTH(
            FOR leadPos IN 0..LENGTH(tokens)-1
              FILTER tokens[leadPos] == phrase[0]
              FILTER LENGTH(FOR i IN 0..LENGTH(phrase)-1
                      FILTER phrase[i] == tokens[leadPos+i]
                      RETURN 1) == LENGTH(phrase)
              RETURN 1) > 0
        SORT d._id
        RETURN d`).toArray();
      assertNotEqual(expected.length, 0);

      {
        let actual = db._query(`
          FOR d IN v_wiki_phrase
            SEARCH PHRASE(d.title, "Lord of The Rings", "tokenizer")
          SORT d._id
          RETURN d`).toArray();

        assertEqual(expected.length, actual.length);
        actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i], rhs)));
      }

      // arguments as bind variables
      {
        let actual = db._query(`
          FOR d IN v_wiki_phrase
            SEARCH PHRASE(d.title, @input, @analyzer)
          SORT d._id
          RETURN d`, { input : "Lord of The Rings", analyzer: "tokenizer"}).toArray();

        assertEqual(expected.length, actual.length);
        actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i], rhs)));
      }

      // arguments as references
      {
        let actual = db._query(`
          LET input = NOOPT("Lord of The Rings")
          LET analyzer = NOOPT("tokenizer")
          FOR d IN v_wiki_phrase
            SEARCH PHRASE(d.title, input, analyzer)
          SORT d._id
          RETURN d`).toArray();

        assertEqual(expected.length, actual.length);
        actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i], rhs)));
      }

      // arguments as an array
      {
        let actual = db._query(`
          LET input = "Lord of The Rings"
          LET analyzer = "tokenizer"
          FOR d IN v_wiki_phrase
            SEARCH PHRASE(d.title, [input], analyzer)
          SORT d._id
          RETURN d`).toArray();
  
        assertEqual(expected.length, actual.length);
        actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i], rhs)));
      }

      // arguments as an array
      {
        let actual = db._query(`
          LET analyzer = "tokenizer"
          FOR d IN v_wiki_phrase
            SEARCH PHRASE(d.title, ["Lord", 0, "of", "The", "Rings"], analyzer)
          SORT d._id
          RETURN d`).toArray();

        assertEqual(expected.length, actual.length);
        actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i], rhs)));
      }

      // arguments as an array
      {
        let actual = db._query(`
          LET input = NOOPT("Lord of The Rings")
          LET analyzer = "tokenizer"
          FOR d IN v_wiki_phrase
            SEARCH PHRASE(d.title, [input], analyzer)
          SORT d._id
          RETURN d`).toArray();

        assertEqual(expected.length, actual.length);
        actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i], rhs)));
      }

      // arguments as a reference
      {
        let actual = db._query(`
          LET analyzer = "tokenizer"
          LET phraseStruct = NOOPT(["Lord", 0, "of", "The", "Rings"])
          FOR d IN v_wiki_phrase
            SEARCH PHRASE(d.title, phraseStruct, analyzer)
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

jsunity.run(ArangoSearch_PHRASE);
if (false === jsunity.done().status) {
  throw "fail";
}
