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
/// @author Andrei Lobov
////////////////////////////////////////////////////////////////////////////////

const jsunity = require("jsunity");
const {assertEqual, assertTrue} = jsunity.jsUnity.assertions;
const db = require("@arangodb").db;
const path = require('path');
const levenshtein = require(path.join(__dirname, "/tests/arangosearch/3rdparty/js-levenshtein/index.js"));
const damlev = require(path.join(__dirname, "/tests/arangosearch/3rdparty/damerau-levenshtein-js/app.js"));
const {query} = require('@arangodb');
const analyzers = require("@arangodb/analyzers");

const maxLevenshteinDistance = 4;
const maxDamerayLevenshteinDistance = 3;

////////////////////////////////////////////////////////////////////////////////
/// @brief test suite
////////////////////////////////////////////////////////////////////////////////

function arangoSearchMatchers () {
  function doLevenshteinTest (resFilterDameray, allCursor, pattern, field, analyzer) {
    let levenshteinMatched = {};
    let damerayLevenshteinMatched = {};
    let i = 0;
    // process all collection and recalc distances with 3rdparty algorithms
    while (allCursor.hasNext()) {
      let val = allCursor.next();
      let minLevenshteinDistance = maxLevenshteinDistance + 1; // not matched by default
      let minDamerayDistance = maxDamerayLevenshteinDistance + 1;
      for (let t in val.tokens) {
        let tokenDistance = levenshtein(pattern, val.tokens[t]);
        if (tokenDistance <= maxLevenshteinDistance) {
          if (minLevenshteinDistance > tokenDistance) {
            minLevenshteinDistance = tokenDistance;
          }
          if (tokenDistance === 0) {
            // best possible match found
            minDamerayDistance = 0;
            break;
          }
        }
        if (minDamerayDistance > 0) {
          let tokenDamerayDistance = damlev.distance(pattern, val.tokens[t]);
          if (tokenDamerayDistance < minDamerayDistance) {
            minDamerayDistance = tokenDamerayDistance;
          }
        }
      }
      if (minDamerayDistance <= maxDamerayLevenshteinDistance) {
        // at same time we could check our dameray-levenshtein implementation
        // FIXME: docs says LEVENSHTEIN_DISTANCE calculates levenshtein
        // but actually it is dameray-levenshtein. So check is here. It is decided
        // to fix in docs eventually.
        assertTrue(i < resFilterDameray.length, val.cout + " is missing from FILTER");
        assertEqual(resFilterDameray[i].count, val.count, "FILTER failed");
        assertEqual(resFilterDameray[i].dist, minDamerayDistance, "FILTER min dist mismatch");
        damerayLevenshteinMatched[val.count] = minDamerayDistance;
        i++;
      }
      if (minLevenshteinDistance <= maxLevenshteinDistance) {
        levenshteinMatched[val.count] = minLevenshteinDistance;
      }
    }
    assertEqual(i, resFilterDameray.length);
    // now check search results for all supported distances
    for (let distance = 0; distance <= maxLevenshteinDistance; ++distance) {
      let res = db._query("FOR d IN view_content SEARCH ANALYZER(LEVENSHTEIN_MATCH(d." +
                          field + ", '" + pattern + "', " + distance + ", false, 0), '" +
                          analyzer + "') " + " SORT d.count RETURN d").toArray();
      let j = 0;
      let count = 0;
      for (let key in levenshteinMatched) {
        if (levenshteinMatched[key] <= distance) {
          count++;
        }
      }
      assertEqual(res.length, count);
      while (j < res.length) {
        assertTrue(levenshteinMatched[res[j].count] <= distance);
        ++j;
      }
    }
    for (let distance = 0; distance <= maxDamerayLevenshteinDistance; ++distance) {
      let res = db._query("FOR d IN view_content SEARCH ANALYZER(LEVENSHTEIN_MATCH(d." +
                          field + ", '" + pattern + "', " + distance + ", true, 0), '" +
                          analyzer + "') " + " SORT d.count RETURN d").toArray();
      let count = 0;
      for (let key in damerayLevenshteinMatched) {
        if (damerayLevenshteinMatched[key] <= distance) {
          count++;
        }
      }
      let j = 0;
      assertEqual(res.length, count);
      while (j < res.length) {
        assertTrue(damerayLevenshteinMatched[res[j].count] <= distance);
        ++j;
      }
    }
  }
  function doStartsWithTest (patterns, cursor, searchRes, match) {
    let i = 0;
    while (cursor.hasNext()) {
      let found = 0;
      let val = cursor.next();
      for (let t in val.tokens) {
        let strToken = String(val.tokens[t]);
        for (let p in patterns) {
          if (strToken.indexOf(patterns[p]) === 0) {
            found++;
            if (found >= match) {
              break;
            }
          }
        }
        if (found >= match) {
          assertTrue(i < searchRes.length, "Document:" + val.count + " is missing from search");
          assertEqual(val.count, searchRes[i].count, "Document:" + val.count + " is missing from search");
          i++;
          break;
        }
      }
    }
    assertEqual(i, searchRes.length);
  }
  return {
    setUpAll: function () {
      try { db._dropView("view_content"); } catch {}
      try { analyzers.remove("my_delimiter", true); } catch {}
      analyzers.save("my_delimiter", "delimiter", {"delimiter": " "});
      db._createView("view_content", "arangosearch",
                     { links: { wikipedia: {
                                            includeAllFields: true,
                                            fields: {
                                                     title: {analyzers: ['identity']},
                                                     body: {analyzers: ['identity', 'my_delimiter']}
                                            }}}});
      // view sync
      db._query("FOR d IN view_content OPTIONS { waitForSync: true } LIMIT 1 RETURN d").toArray();
    },
    tearDownAll: function () {
      try { db._dropView("view_content"); } catch {}
      analyzers.remove("my_delimiter", true);
    },
    testTestPrefix: function () {
      let pattern = "'Anarch%'";
      let res = db._query("FOR d IN view_content SEARCH ANALYZER(LIKE(d.title, " +
                          pattern + "), 'identity') SORT d.count RETURN d").toArray();
      let resFilter = db._query("FOR d IN wikipedia FILTER LIKE(d.title, " + pattern +
                                ") SORT d.count RETURN d").toArray();
      assertEqual(resFilter.length, res.length);
      for (let i = 0; i < resFilter.length; ++i) {
        assertEqual(resFilter[i]._key, res[i]._key);
      }
    },
    testTestPostfix: function () {
      let pattern = "'%arch'";
      let res = db._query("FOR d IN view_content SEARCH ANALYZER(LIKE(d.title, " +
                          pattern + "), 'identity') SORT d.count RETURN d").toArray();
      let resFilter = db._query("FOR d IN wikipedia FILTER LIKE(d.title, " +
                                pattern + ") SORT d.count RETURN d").toArray();
      assertEqual(resFilter.length, res.length);
      for (let i = 0; i < resFilter.length; ++i) {
        assertEqual(resFilter[i]._key, res[i]._key);
      }
    },
    testTestMiddle: function () {
      let pattern = "'%arc%'";
      let res = db._query("FOR d IN view_content SEARCH ANALYZER(LIKE(d.title, " +
                          pattern + "), 'identity') SORT d.count RETURN d").toArray();
      let resFilter = db._query("FOR d IN wikipedia FILTER LIKE(d.title, " +
                                pattern + ") SORT d.count RETURN d").toArray();
      assertEqual(resFilter.length, res.length);
      for (let i = 0; i < resFilter.length; ++i) {
        assertEqual(resFilter[i]._key, res[i]._key);
      }
    },
    testTestMiddleWithVariables: function () {
      let pattern = "'%arc%'";
      let res = db._query("FOR p IN [" + pattern + "] FOR d IN view_content SEARCH ANALYZER(LIKE(d.title, p), " +
                          "'identity') SORT d.count RETURN d").toArray();
      let resFilter = db._query("FOR d IN wikipedia FILTER LIKE(d.title, " +
                                pattern + ") SORT d.count RETURN d").toArray();
      assertEqual(resFilter.length, res.length);
      for (let i = 0; i < resFilter.length; ++i) {
        assertEqual(resFilter[i]._key, res[i]._key);
      }
    },
    testTestMiddleMixedPlaceholders: function () {
      let pattern = "'%a%_r_c%'";
      let res = db._query("FOR d IN view_content SEARCH ANALYZER(d.title LIKE " + pattern +
                          ", 'identity') SORT d.count RETURN d").toArray();
      let resFilter = db._query("FOR d IN wikipedia FILTER LIKE(d.title, " + pattern +
                                ") SORT d.count RETURN d").toArray();
      assertEqual(resFilter.length, res.length);
      for (let i = 0; i < resFilter.length; ++i) {
        assertEqual(resFilter[i]._key, res[i]._key);
      }
    },
    testTestMiddleWithWords: function () {
      let pattern = "'%Lord%Rings%'";
      let res = db._query("FOR d IN view_content SEARCH ANALYZER(d.title LIKE " + pattern +
                          ", 'identity') SORT d.count RETURN d").toArray();
      let resFilter = db._query("FOR d IN wikipedia FILTER LIKE(d.title, " + pattern +
                                ") SORT d.count RETURN d").toArray();
      assertEqual(resFilter.length, res.length);
      for (let i = 0; i < resFilter.length; ++i) {
        assertEqual(resFilter[i]._key, res[i]._key);
      }
    },
    testTestBody: function () {
      let pattern = "'%Lord________Rings%'";
      let res = db._query("FOR d IN view_content SEARCH ANALYZER(d.body LIKE " + pattern +
                          ", 'identity') SORT d.count RETURN d").toArray();
      let resFilter = db._query("FOR d IN wikipedia FILTER LIKE(d.body, " + pattern +
                                ") SORT d.count RETURN d").toArray();
      assertEqual(resFilter.length, res.length);
      for (let i = 0; i < resFilter.length; ++i) {
        assertEqual(resFilter[i]._key, res[i]._key);
      }
    },
    testTestBodyPrefix: function () {
      let pattern = "'The_%a%'";
      let res = db._query("FOR d IN view_content SEARCH ANALYZER(d.body LIKE " + pattern +
                          ", 'identity') SORT d.count RETURN d").toArray();
      let resFilter = db._query("FOR d IN wikipedia FILTER LIKE(d.body, " + pattern +
                                ") SORT d.count RETURN d").toArray();
      assertEqual(resFilter.length, res.length);
      for (let i = 0; i < resFilter.length; ++i) {
        assertEqual(resFilter[i]._key, res[i]._key);
      }
    },
    testTestBodySuffix: function () {
      let pattern = "'_%!'";
      let res = db._query("FOR d IN view_content SEARCH ANALYZER(d.body LIKE " + pattern +
                          ", 'identity') SORT d.count RETURN d").toArray();
      let resFilter = db._query("FOR d IN wikipedia FILTER LIKE(d.body, " + pattern +
                                ") SORT d.count RETURN d").toArray();
      assertEqual(resFilter.length, res.length);
      for (let i = 0; i < resFilter.length; ++i) {
        assertEqual(resFilter[i]._key, res[i]._key);
      }
    },
    testLevenshteinMatch () {
      const pattern = 'automaton';
      var resFilterDameray = db._query(" FOR d IN wikipedia LET matched =  " +
                                       " MIN(FOR t IN TOKENS(d.body, 'my_delimiter') " +
                                       " LET dist = LEVENSHTEIN_DISTANCE(t, '" + pattern + "') " +
                                       " FILTER dist <= " + maxDamerayLevenshteinDistance +
                                       " RETURN dist) FILTER NOT IS_NULL(matched) SORT d.count " +
                                       " RETURN {count: d.count, dist: matched}").toArray();
      const cursor = query`FOR d IN wikipedia SORT d.count RETURN {count: d.count, tokens: TOKENS(d.body, 'my_delimiter')}`;
      doLevenshteinTest(resFilterDameray, cursor, pattern, "body", "my_delimiter");
    },
    testLevenshteinMatchFilterFallback () {
      const pattern = 'automaton';
      const distance = maxLevenshteinDistance + 1;
      // check fallback implementation of LEVENTSHTEIN_MATCH for long distance
      let resFilter = db._query("FOR d IN wikipedia FILTER LEVENSHTEIN_MATCH(d.title, '" +
                                pattern + "', " + distance + ") SORT d.count RETURN d").toArray();
      const cursor = query`FOR d IN wikipedia SORT d.count RETURN d`;
      let i = 0;
      while (cursor.hasNext()) {
        let val = cursor.next();
        let tokenDistance = levenshtein(pattern, val.title);
        if (tokenDistance <= distance) {
          assertTrue(i < resFilter.length);
          assertEqual(val.count, resFilter[i].count);
          ++i;
        }
      }
      assertEqual(i, resFilter.length);
    },
    testLevenshteinMatchFilterFallbackWithVariables () {
      const pattern = 'automaton';
      const distance = maxLevenshteinDistance + 1;
      // check fallback implementation of LEVENTSHTEIN_MATCH for long distance
      let resFilter = db._query("LET p = '" + pattern + "' FOR dist IN " + distance + ".." + distance +
                                " FOR d IN wikipedia FILTER LEVENSHTEIN_MATCH(d.title, NOOPT(p), NOOPT(dist)) SORT d.count RETURN d").toArray();
      const cursor = query`FOR d IN wikipedia SORT d.count RETURN d`;
      let i = 0;
      while (cursor.hasNext()) {
        let val = cursor.next();
        let tokenDistance = levenshtein(pattern, val.title);
        if (tokenDistance <= distance) {
          assertTrue(i < resFilter.length);
          assertEqual(val.count, resFilter[i].count);
          ++i;
        }
      }
      assertEqual(i, resFilter.length);
    },
    testBm25Relevance () {
      const pattern = 'automaton';
      for (let distance = 0; distance <= maxLevenshteinDistance; ++distance) {
        let res = db._query(" FOR d IN view_content SEARCH LEVENSHTEIN_MATCH(d.title, '" +
                            pattern + "', " + distance + ", false, 0 )" +
                            " SORT BM25(d) DESC RETURN d").toArray();
        let prevDistance = 0;
        res.forEach(doc => {
          let ld = levenshtein(doc.title, pattern);
          assertTrue(ld >= prevDistance);
          prevDistance = ld;
        });
      }
      for (let distance = 0; distance <= maxDamerayLevenshteinDistance; ++distance) {
        let res = db._query(" FOR d IN view_content SEARCH LEVENSHTEIN_MATCH(d.title, '" +
                            pattern + "', " + distance + ", true, 0 )" +
                            " SORT BM25(d) DESC RETURN d").toArray();
        let prevDistance = 0;
        res.forEach(doc => {
          let dld = damlev.distance(doc.title, pattern);
          assertTrue(dld >= prevDistance);
          prevDistance = dld;
        });
      }
    },
    testTFIDFRelevance () {
      const pattern = 'automaton';
      for (let distance = 0; distance <= maxLevenshteinDistance; ++distance) {
        let res = db._query(" FOR d IN view_content SEARCH LEVENSHTEIN_MATCH(d.title, '" +
                            pattern + "', " + distance + ", false, 0 )" +
                            " SORT TFIDF(d) DESC RETURN d").toArray();
        let prevDistance = 0;
        res.forEach(doc => {
          let ld = levenshtein(doc.title, pattern);
          assertTrue(ld >= prevDistance);
          prevDistance = ld;
        });
      }
      for (let distance = 0; distance <= maxDamerayLevenshteinDistance; ++distance) {
        let res = db._query(" FOR d IN view_content SEARCH LEVENSHTEIN_MATCH(d.title, '" +
                            pattern + "', " + distance + ", true, 0 )" +
                            " SORT TFIDF(d) DESC RETURN d").toArray();
        let prevDistance = 0;
        res.forEach(doc => {
          let dld = damlev.distance(doc.title, pattern);
          assertTrue(dld >= prevDistance);
          prevDistance = dld;
        });
      }
    },
    testFromSubquery: function () {
      let patterns = db._query("RETURN TOKENS('Quick brown fox jumps over lazy dog', 'text_en')").toArray();
      let res = db._query(" LET tokens = " +
                          "   (FOR c IN TOKENS('Quick brown fox jumps over lazy dog', 'text_en') RETURN c) " +
                          " FOR d in view_content " +
                          " SEARCH ANALYZER(STARTS_WITH(d.body, tokens, LENGTH(tokens)), 'my_delimiter') " +
                          " SORT d.count RETURN d").toArray();
      const cursor = query`FOR d IN wikipedia SORT d.count RETURN {count: d.count, tokens: TOKENS(d.body, 'my_delimiter')}`;
      doStartsWithTest(patterns, cursor, res);
    },
    testInSubquery: function () {
      let patterns = ['Ameri', 'Quick', 'Slow'];
      let res = db._query("FOR c IN ['Ameri', 'Quick', 'Slow'] " +
                          "FOR d IN view_content " +
                          "SEARCH ANALYZER(STARTS_WITH(d.title, c, 1), 'identity')" +
                          "SORT d.count RETURN d ").toArray();
      const cursor = query`FOR d IN wikipedia SORT d.count RETURN {count: d.count, tokens: [d.title]}`;
      doStartsWithTest(patterns, cursor, res, 1);
    },
    testArrayOfArrays: function () {
      let patterns = [['Ameri', 'Quick', 'Slow'], ['Fast', 'Long'], ['Offs', 'Suff']];
      let res = db._query("FOR c IN [['Ameri', 'Quick', 'Slow'], ['Fast', 'Long'], ['Offs', 'Suff']] " +
                          "FOR d IN view_content " +
                          "SEARCH ANALYZER(STARTS_WITH(d.body, c, LENGTH(c)), 'my_delimiter') " +
                          " SORT d.count RETURN d").toArray();
      const cursor = query`FOR d IN wikipedia SORT d.count RETURN {count: d.count, tokens: TOKENS(d.body, 'my_delimiter')}`;
      let i = 0;
      while (cursor.hasNext()) {
        let found = true;
        let val = cursor.next();
        for (let t in val.tokens) {
          let strToken = String(val.tokens[t]);
          for (let p in patterns) {
            found = true;
            for (let s in patterns[p]) {
              if (strToken.indexOf(patterns[p][s]) !== 0) {
                found = false;
                break;
              }
            }
            if (!found) {
              break;
            }
          }
          if (found) {
            assertTrue(i < res.length, "Document:" + val.count + " is missing from search");
            assertEqual(val.count, res[i].count);
            i++;
            break;
          }
        }
      }
      assertEqual(i, res.length);
    },
    testFromConstArrayFullMatch: function () {
      let patterns = ["Anarch", "Anar", "An"];
      let res = db._query(" FOR d in view_content " +
                          " SEARCH ANALYZER(STARTS_WITH(d.title, ['Anarch', 'Anar', 'An'], 3), 'identity') " +
                          " SORT d.count RETURN d").toArray();
      const cursor = query`FOR d IN wikipedia SORT d.count RETURN {count: d.count, tokens: [d.title]}`;
      doStartsWithTest(patterns, cursor, res, 3);
    },
    testFromConstArrayOneMatch: function () {
      let patterns = ["Anarch", "Auto", "Ameri"];
      let res = db._query(" FOR d in view_content " +
                          " SEARCH ANALYZER(STARTS_WITH(d.title, ['Anarch', 'Auto', 'Ameri'], 1), 'identity') " +
                          " SORT d.count RETURN d").toArray();
      const cursor = query`FOR d IN wikipedia SORT d.count RETURN {count: d.count, tokens: [d.title]}`;
      doStartsWithTest(patterns, cursor, res, 1);
    },
    testStringTest: function () {
      let pattern = "Anarch";
      let res = db._query(" FOR d in view_content " +
                          "  SEARCH ANALYZER(STARTS_WITH(d.title, '" + pattern + "'), 'identity') " +
                          " SORT d.count RETURN d").toArray();
      const cursor = query`FOR d IN wikipedia SORT d.count RETURN {count: d.count, tokens: [d.title] }`;
      doStartsWithTest([pattern], cursor, res, 1);
    }
  };
}

////////////////////////////////////////////////////////////////////////////////
/// @brief executes the test suite
////////////////////////////////////////////////////////////////////////////////

jsunity.run(arangoSearchMatchers);
if (false === jsunity.done().status) {
  throw "fail";
}
