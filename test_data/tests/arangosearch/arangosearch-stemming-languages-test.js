/* jshint globalstrict:false, strict:false, maxlen: 500 */

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
const analyzers = require("@arangodb/analyzers");
const {assertTrue} = jsunity.jsUnity.assertions;
const db = require("@arangodb").db;
const path = require('path');
const _ = require('lodash');

////////////////////////////////////////////////////////////////////////////////
/// @brief test suite
////////////////////////////////////////////////////////////////////////////////

function arangoSearchStemmingLanguages () {
  function doTest (localeName, input, expected, expectedEdgeNgram) {
    const analyzerName = "stemminAnalyzerTest";
    const analyzerEdgeName = "stemminEdgeAnalyzerTest";
    try { analyzers.remove(analyzerName, true); } catch {}
    try { analyzers.remove(analyzerEdgeName, true); } catch {}
    try {
      analyzers.save(analyzerName, "text", { locale: localeName,
                                             stemming: true,
                                             accent: false,
                                             stopwords: [],
                                             case: "none" });
      analyzers.save(analyzerEdgeName, "text", { locale: localeName,
                                                 stemming: false,
                                                 stopwords: [],
                                                 accent: false,
                                                 case: "lower",
                                                 edgeNgram: { min: 2,
                                                              max: 3,
                                                              preserveOriginal: true }});
      let res = db._query("RETURN TOKENS('" + input + "', '" + analyzerName + "')").toArray();
      let resEdgeNgram = db._query("RETURN TOKENS('" + input +
                                   "', '" + analyzerEdgeName + "')").toArray();
      assertTrue(_.isEqual(res[0], expected));
      assertTrue(_.isEqual(resEdgeNgram[0], expectedEdgeNgram));
    } finally {
      try { analyzers.remove(analyzerName, true); } catch {}
      try { analyzers.remove(analyzerEdgeName, true); } catch {}
    }
  }
  return {
    testArabic: function () {
      doTest("ar_Arab_EG.UTF-8", "الرياضيين", ["رياض"], ["ال", "الر", "الرياضيين"]);
    },
    testBasque: function () {
      doTest("eu_ES.UTF-8", "Kirolariak", ["Kiro"], ["ki", "kir", "kirolariak"]);
    },
    testCatalan: function () {
      doTest("ca_ES.UTF-8", "Esportistes", ["Esport"], ["es", "esp", "esportistes"]);
    },
    testDanish: function () {
      doTest("da_DK.UTF-8", "Atleter", ["Atlet"], ["at", "atl", "atleter"]);
    },
    testGreek: function () {
      doTest("el_GR.UTF-8", "Αθλητές", [ "Aθλητ" ], [ "αθ", "αθλ", "αθλητες" ]);
      // FIXME: looks like a bug in ICU   ^ A should not be converted here
    },
    testHindi: function () {
      doTest("hi_IN.UTF-8", "\u090F\u0925\u0932\u0940\u091F", [ "\u090F\u0925\u0932\u0940\u091F" ],
             [ "\u090F\u0925", "\u090F\u0925\u0932", "\u090F\u0925\u0932\u0940\u091F" ]);
    },
    testHungarian: function () {
      doTest("hu_HU.UTF-8", "Sportoló", ["Sportol"], ["sp", "spo", "sportolo"]);
    },
    testIndonesian: function () {
      doTest("id_ID.UTF-8", "Atlet", ["Atlet"], ["at", "atl", "atlet"]);
    },
    testIrish: function () {
      doTest("ga_IE.UTF-8", "Lúthchleasaithe", ["Luthchleasaithe"], ["lu", "lut", "luthchleasaithe"]);
    },
    testLithuanian: function () {
      doTest("lt_LT.UTF-8", "Sportininkai", ["Sportinink"], ["sp", "spo", "sportininkai"]);
    },
    testNepali: function () {
      doTest("ne_NP.UTF-8", "खेलाडीहरू", ["\u0916\u0932\u093e\u0921\u0940\u0939\u0930"],
             ["\u0916\u0932", "\u0916\u0932\u093e", "\u0916\u0932\u093e\u0921\u0940\u0939\u0930"]);
    },
    testRomanian: function () {
      doTest("ro_RO.UTF-8", "Sportivii", ["Sportiv"], ["sp", "spo", "sportivii"]);
    },
    testSerbian: function () {
      doTest("sr_RS.UTF-8", "Спортисти", ["Сportist"], ["сп", "спо", "спортисти"]);
    },
    testTamil: function () {
      doTest("ta_IN.UTF-8", "மரங்கள்",
             ["\u0bae\u0bb0\u0b99\u0b95\u0bb3"],
             ["\u0bae\u0bb0", "\u0bae\u0bb0\u0b99",
              "\u0bae\u0bb0\u0b99\u0b95\u0bb3"]);
    },
    testTurkish: function () {
      doTest("tr_TR.UTF-8", "Ağaçlar", ["Agac"], ["ag", "aga", "agaclar"]);
    }
  };
}

////////////////////////////////////////////////////////////////////////////////
/// @brief executes the test suite
////////////////////////////////////////////////////////////////////////////////

jsunity.run(arangoSearchStemmingLanguages);
if (false === jsunity.done().status) {
  throw "fail";
}
