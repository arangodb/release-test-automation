/* global print, semver, progress, createCollectionSafe, db, fs, PWD */
/*jslint maxlen: 130 */

const { count } = require("console");
const { stringify } = require("querystring");

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
      print(`making per database data ${dbCount}`);

      //creation computed values with sample collections
      let c1 = `c1_${dbCount}`;
      let a1 = createCollectionSafe(c1, 3, 3);
      a1.properties({ computedValues: [{ "name": "default", "expression": "RETURN SOUNDEX('sky')", overwrite: true }] });

      let c2 = `c2_${dbCount}`;
      let a2 = createCollectionSafe(c2, 3, 3);
      a2.properties({ computedValues: [{ "name": "default", "expression": "RETURN SOUNDEX('dog')", overwrite: true }] });

      let c3_insert = `c3_insert_${dbCount}`;
      let a3 = createCollectionSafe(c3_insert, 3, 3);
      a3.properties({ computedValues: [{ "name": "default_insert", "expression": "RETURN SOUNDEX('frog')", computeOn: ["insert"], overwrite: true }] });

      let c4_update = `c4_update_${dbCount}`;
      let a4 = createCollectionSafe(c4_update, 3, 3);
      a4.properties({ computedValues: [{ "name": "default_update", "expression": "RETURN SOUNDEX('beer')", computeOn: ["update"], overwrite: true }] });

      let c5_replace = `c5_replace_${dbCount}`;
      let a5 = createCollectionSafe(c5_replace, 3, 3);
      a5.properties({ computedValues: [{ "name": "default_replace", "expression": "RETURN SOUNDEX('water')", computeOn: ["replace"], overwrite: true }] });

      let c6_not_null = `c6_not_null_${dbCount}`;
      let a6 = createCollectionSafe(c6_not_null, 3, 3);
      a6.properties({ computedValues: [{ "name": "default", "expression": "RETURN null", overwrite: true, keepNull: false }] });

      let c7_hex = `c7_hex_${dbCount}`;
      let a7 = createCollectionSafe(c7_hex, 3, 3);
      a7.properties({ computedValues: [{ "name": "default", "expression": "RETURN TO_HEX(@doc.name)", overwrite: true }] });

      let c8_overwriteFalse = `c8_overwriteFalse_${dbCount}`;
      let a8 = createCollectionSafe(c8_overwriteFalse, 3, 3);
      a8.properties({ computedValues: [{ "name": "default", "expression": "RETURN CONCAT('42_', TO_STRING(@doc.field))", overwrite: false }] });

      let c9_overwriteTrue = `c9_overwriteTrue_${dbCount}`;
      let a9 = createCollectionSafe(c9_overwriteTrue, 3, 3);
      a9.properties({ computedValues: [{ "name": "default", "expression": "RETURN CONCAT('42_', TO_STRING(@doc.field))", overwrite: true }] });

      let c10_multiple = `c10_multiple_${dbCount}`;
      let a10 = createCollectionSafe(c10_multiple, 3, 3);
      a10.properties({ computedValues: [{ "name": "default1", "expression": "RETURN 'foo'", overwrite: true }, { "name": "default2", "expression": "RETURN 'bar'", overwrite: true }, { "name": "default3", "expression": "RETURN 'baz'", overwrite: true }] });

      let c11 = `c11_${dbCount}`;
      let a11 = createCollectionSafe(c11, 3, 3);
      a11.properties({ computedValues: [{ "name": "default", "expression": "RETURN CONCAT(@doc._key, ' ', @doc._id, ' ', @doc._rev)", overwrite: true }] });

      let c12 = `c12_${dbCount}`;
      let a12 = createCollectionSafe(c12, 3, 3);
      a12.properties({ computedValues: [{ "name": "default", "expression": "RETURN [{from_doc: CONCAT(@doc.name, ' ', @doc.field), system:{_key: @doc._key, _rev: @doc._rev, _id: @doc._id}, values: [RANGE(1, 10)]}]", overwrite: true }] });

      //-------------------------------------------------------x-------------------------------------------------------------

      // this function will check Computed Values properties
      function checkComValProperties(comValueName, obj1, obj2) {
        const obj1Length = Object.keys(obj1).length;
        const obj2Length = Object.keys(obj2).length;

        if (obj1Length === obj2Length) {
          return Object.keys(obj1).every(
            (key) => obj2.hasOwnProperty(key)
              && obj2[key] === obj1[key]);
        } else {
          throw new Error(`${comValueName} properties missmatched!`);
        }
      };

      //Perform modification and comparision for desired output of Computed Values
      //for c1 comVal
      let c1_exp_modification = [
        {
          "name": "cv_field",
          "expression": "RETURN SOUNDEX('sky')",
          "computeOn": [
            "insert",
            "update",
            "replace"
          ],
          "overwrite": true,
          "failOnWarning": false,
          "keepNull": true
        }
      ]

      let c1_actual_modification = a1.properties({ computedValues: [{ "name": "cv_field", "expression": "RETURN SOUNDEX('sky')", overwrite: true }] })

      checkComValProperties(c1, c1_exp_modification, c1_actual_modification.computedValues);

      //for c2 comVal
      let c2_exp_modification = [
        {
          "name": "default",
          "expression": "RETURN SOUNDEX('dog')",
          "computeOn": [
            "insert",
            "update",
            "replace"
          ],
          "overwrite": true,
          "failOnWarning": false,
          "keepNull": true
        }

      ]

      let c2_actual_modification = a2.properties({ computedValues: [{ "name": "cv_field", "expression": "RETURN SOUNDEX('dog')", "overwrite": true }] })

      checkComValProperties(c2, c2_exp_modification, c2_actual_modification.computedValues);

      //for c3_insert comVal
      let c3_exp_modification = [
        {
          "name": "default_insert",
          "expression": "RETURN SOUNDEX('frog')",
          "computeOn": [
            "insert"
          ],
          "overwrite": true,
          "failOnWarning": false,
          "keepNull": true
        }
      ]

      let c3_actual_modification = a3.properties({ computedValues: [{ "name": "cv_field_insert", "expression": "RETURN SOUNDEX('frog')", "computeOn": ["insert"], "overwrite": true }] })

      checkComValProperties(c3_insert, c3_exp_modification, c3_actual_modification.computedValues);

      //for c4_update comVal
      let c4_exp_modification = [
        {
          "name": "cv_field_update",
          "expression": "RETURN SOUNDEX('beer')",
          "computeOn": [
            "update"
          ],
          "overwrite": true,
          "failOnWarning": false,
          "keepNull": true
        }
      ]

      let c4_actual_modification = a4.properties({ computedValues: [{ "name": "cv_field_update", "expression": "RETURN SOUNDEX('beer')", "computeOn": ["update"], "overwrite": true }] })

      checkComValProperties(c4_update, c4_exp_modification, c4_actual_modification.computedValues);

      //for c5_replace comVal
      let c5_exp_modification = [
        {
          "name": "cv_field_update",
          "expression": "RETURN SOUNDEX('beer')",
          "computeOn": [
            "update"
          ],
          "overwrite": true,
          "failOnWarning": false,
          "keepNull": true
        }
      ]

      let c5_actual_modification = a5.properties({ computedValues: [{ "name": "cv_field_replace", "expression": "RETURN SOUNDEX('water')", "computeOn": ["replace"], "overwrite": true }] })

      checkComValProperties(c5_replace, c5_exp_modification, c5_actual_modification.computedValues);

      //for c6_not_null comVal
      let c6_exp_modification = [
        {
          "name": "cv_field",
          "expression": "RETURN null",
          "computeOn": [
            "insert",
            "update",
            "replace"
          ],
          "overwrite": true,
          "failOnWarning": false,
          "keepNull": false
        }
      ]

      let c6_actual_modification = a6.properties({ computedValues: [{ "name": "cv_field", "expression": "RETURN null", "overwrite": true, "keepNull": false }] })

      checkComValProperties(c6_not_null, c6_exp_modification, c6_actual_modification.computedValues);

      //for c7_hex comVal
      let c7_exp_modification = [
        {
          "name": "cv_field",
          "expression": "RETURN TO_HEX(@doc.name)",
          "computeOn": [
            "insert",
            "update",
            "replace"
          ],
          "overwrite": true,
          "failOnWarning": false,
          "keepNull": true
        }
      ]

      let c7_actual_modification = a7.properties({ computedValues: [{ "name": "cv_field", "expression": "RETURN TO_HEX(@doc.name)", "overwrite": true }] })

      checkComValProperties(c7_hex, c7_exp_modification, c7_actual_modification.computedValues);

      //for c8_overwriteFalse comVal
      let c8_exp_modification = [
        {
          "name": "cv_field",
          "expression": "RETURN CONCAT('42_', TO_STRING(@doc.field))",
          "computeOn": [
            "insert",
            "update",
            "replace"
          ],
          "overwrite": false,
          "failOnWarning": false,
          "keepNull": true
        }
      ]

      let c8_actual_modification = a8.properties({ computedValues: [{ "name": "cv_field", "expression": "RETURN CONCAT('42_', TO_STRING(@doc.field))", "overwrite": false }] })

      checkComValProperties(c8_overwriteFalse, c8_exp_modification, c8_actual_modification.computedValues);

      //for c9_overwriteTrue comVal
      let c9_exp_modification = [
        {
          "name": "cv_field",
          "expression": "RETURN CONCAT('42_', TO_STRING(@doc.field))",
          "computeOn": [
            "insert",
            "update",
            "replace"
          ],
          "overwrite": false,
          "failOnWarning": false,
          "keepNull": true
        }
      ]

      let c9_actual_modification = a9.properties({ computedValues: [{ "name": "cv_field", "expression": "RETURN CONCAT('42_', TO_STRING(@doc.field))", "overwrite": true }] })

      checkComValProperties(c9_overwriteTrue, c9_exp_modification, c9_actual_modification.computedValues);

      //for c10_multiple comVal
      let c10_exp_modification = [
        {
          "name": "cv_field1",
          "expression": "RETURN 'foo'",
          "computeOn": [
            "insert",
            "update",
            "replace"
          ],
          "overwrite": true,
          "failOnWarning": false,
          "keepNull": true
        },
        {
          "name": "cv_field2",
          "expression": "RETURN 'bar'",
          "computeOn": [
            "insert",
            "update",
            "replace"
          ],
          "overwrite": true,
          "failOnWarning": false,
          "keepNull": true
        },
        {
          "name": "cv_field3",
          "expression": "RETURN 'baz'",
          "computeOn": [
            "insert",
            "update",
            "replace"
          ],
          "overwrite": true,
          "failOnWarning": false,
          "keepNull": true
        }
      ]

      let c10_actual_modification = a10.properties({ computedValues: [{ "name": "cv_field1", "expression": "RETURN 'foo'", "overwrite": true }, { "name": "cv_field2", "expression": "RETURN 'bar'", "overwrite": true }, { "name": "cv_field3", "expression": "RETURN 'baz'", "overwrite": true }] })

      checkComValProperties(c10_multiple, c10_exp_modification, c10_actual_modification.computedValues);

      //for c11 comVal
      let c11_exp_modification = [
        {
          "name": "cv_field",
          "expression": "RETURN CONCAT(@doc._key, ' ', @doc._id, ' ', @doc._rev)",
          "computeOn": [
            "insert",
            "update",
            "replace"
          ],
          "overwrite": true,
          "failOnWarning": false,
          "keepNull": true
        }
      ]

      let c11_actual_modification = a11.properties({ computedValues: [{ "name": "cv_field", "expression": "RETURN CONCAT(@doc._key, ' ', @doc._id, ' ', @doc._rev)", "overwrite": true }] })

      checkComValProperties(c11, c11_exp_modification, c11_actual_modification.computedValues);

      //for c12_overwriteTrue comVal
      let c12_exp_modification = [
        {
          "name": "cv_field",
          "expression": "RETURN CONCAT(@doc._key, ' ', @doc._id, ' ', @doc._rev)",
          "computeOn": [
            "insert",
            "update",
            "replace"
          ],
          "overwrite": true,
          "failOnWarning": false,
          "keepNull": true
        }
      ]

      let c12_actual_modification = a12.properties({ computedValues: [{ "name": "cv_field", "expression": "RETURN [{from_doc: CONCAT(@doc.name, ' ', @doc.field), system:{_key: @doc._key, _rev: @doc._rev, _id: @doc._id}, values: [RANGE(1, 10)]}]", "overwrite": true }] })

      checkComValProperties(c12, c12_exp_modification, c12_actual_modification.computedValues);

      //-------------------------------------------------------x-------------------------------------------------------------

      // creating indexes for the collections
      a1.ensureIndex({"type":"inverted","name":"inverted","fields":[{"name":"cv_field"}]})
      a1.ensureIndex({"type":"persistent","name":"persistent","fields":["cv_field"], "sparse": true})

      a2.ensureIndex({"type":"inverted","name":"inverted","fields":[{"name":"cv_field"}]})
      a2.ensureIndex({"type":"persistent","name":"persistent","fields":["cv_field"], "sparse": true})

      a3.ensureIndex({"type":"inverted","name":"inverted","fields":[{"name":"cv_field"}, "cv_field_insert"]})
      a3.ensureIndex({"type":"persistent","name":"persistent","fields":["cv_field"], "sparse": true})

      a4.ensureIndex({"type":"inverted","name":"inverted","fields":[{"name":"cv_field"}]})
      a4.ensureIndex({"type":"persistent","name":"persistent","fields":["cv_field"], "sparse": true})

      a5.ensureIndex({"type":"inverted","name":"inverted","fields":[{"name":"cv_field"}]})
      a5.ensureIndex({"type":"persistent","name":"persistent","fields":["cv_field"], "sparse": true})

      a6.ensureIndex({"type":"inverted","name":"inverted","fields":[{"name":"cv_field"}]})
      a6.ensureIndex({"type":"persistent","name":"persistent","fields":["cv_field"], "sparse": true})

      a7.ensureIndex({"type":"inverted","name":"inverted","fields":[{"name":"cv_field"}]})
      a7.ensureIndex({"type":"persistent","name":"persistent","fields":["cv_field"], "sparse": true})

      a8.ensureIndex({"type":"inverted","name":"inverted","fields":[{"name":"cv_field"}]})
      a8.ensureIndex({"type":"persistent","name":"persistent","fields":["cv_field"], "sparse": true})

      a9.ensureIndex({"type":"inverted","name":"inverted","fields":[{"name":"cv_field"}]})
      a9.ensureIndex({"type":"persistent","name":"persistent","fields":["cv_field"], "sparse": true})

      a10.ensureIndex({"type":"inverted","name":"inverted","fields":[{"name":"cv_field1"},{"name":"cv_field2"},{"name":"cv_field3"}]})
      a10.ensureIndex({"type":"persistent","name":"persistent","fields":["cv_field1", "cv_field2", "cv_field3"], "sparse": true})

      a11.ensureIndex({"type":"inverted","name":"inverted","fields":[{"name":"cv_field"}]})
      a11.ensureIndex({"type":"persistent","name":"persistent","fields":["cv_field"], "sparse": true})

      a12.ensureIndex({"type":"inverted","name":"inverted","fields":[{"name":"cv_field", "nested": ["from_doc"]}]})
      
      //-------------------------------------------------------x-------------------------------------------------------------

      // creating views for the collections
      db._createView("testView", "arangosearch")

      let queryOutput = db.testView.properties(
        {"links":{
          "c1_0":{"includeAllFields":true},
          "c2_0":{"includeAllFields":true},
          "c3_insert_0":{"includeAllFields":true},
          "c4_update_0":{"includeAllFields":true},
          "c5_replace_0":{"includeAllFields":true},
          "c6_not_null_0":{"includeAllFields":true},
          "c7_hex_0":{"includeAllFields":true},
          "c8_overwriteFalse_0":{"includeAllFields":true},
          "c9_overwriteTrue_0":{"includeAllFields":true},
          "c10_multiple_0":{"includeAllFields":true},
          "c11_0":{"includeAllFields":true},
          "c12_0":{"includeAllFields":true}
        }
      })

      expected_output = {
        "cleanupIntervalStep" : 2,
        "commitIntervalMsec" : 1000,
        "consolidationIntervalMsec" : 1000,
        "consolidationPolicy" : {
          "type" : "tier",
          "segmentsBytesFloor" : 2097152,
          "segmentsBytesMax" : 5368709120,
          "segmentsMax" : 10,
          "segmentsMin" : 1,
          "minScore" : 0
        },
        "primarySort" : [ ],
        "primarySortCompression" : "lz4",
        "storedValues" : [ ],
        "writebufferActive" : 0,
        "writebufferIdle" : 64,
        "writebufferSizeMax" : 33554432,
        "links" : {
          "c1_0" : {
            "analyzers" : [
              "identity"
            ],
            "fields" : {
            },
            "includeAllFields" : true,
            "storeValues" : "none",
            "trackListPositions" : false
          },
          "c2_0" : {
            "analyzers" : [
              "identity"
            ],
            "fields" : {
            },
            "includeAllFields" : true,
            "storeValues" : "none",
            "trackListPositions" : false
          },
          "c3_insert_0" : {
            "analyzers" : [
              "identity"
            ],
            "fields" : {
            },
            "includeAllFields" : true,
            "storeValues" : "none",
            "trackListPositions" : false
          },
          "c4_update_0" : {
            "analyzers" : [
              "identity"
            ],
            "fields" : {
            },
            "includeAllFields" : true,
            "storeValues" : "none",
            "trackListPositions" : false
          },
          "c5_replace_0" : {
            "analyzers" : [
              "identity"
            ],
            "fields" : {
            },
            "includeAllFields" : true,
            "storeValues" : "none",
            "trackListPositions" : false
          },
          "c6_not_null_0" : {
            "analyzers" : [
              "identity"
            ],
            "fields" : {
            },
            "includeAllFields" : true,
            "storeValues" : "none",
            "trackListPositions" : false
          },
          "c7_hex_0" : {
            "analyzers" : [
              "identity"
            ],
            "fields" : {
            },
            "includeAllFields" : true,
            "storeValues" : "none",
            "trackListPositions" : false
          },
          "c8_overwriteFalse_0" : {
            "analyzers" : [
              "identity"
            ],
            "fields" : {
            },
            "includeAllFields" : true,
            "storeValues" : "none",
            "trackListPositions" : false
          },
          "c9_overwriteTrue_0" : {
            "analyzers" : [
              "identity"
            ],
            "fields" : {
            },
            "includeAllFields" : true,
            "storeValues" : "none",
            "trackListPositions" : false
          },
          "c10_multiple_0" : {
            "analyzers" : [
              "identity"
            ],
            "fields" : {
            },
            "includeAllFields" : true,
            "storeValues" : "none",
            "trackListPositions" : false
          },
          "c11_0" : {
            "analyzers" : [
              "identity"
            ],
            "fields" : {
            },
            "includeAllFields" : true,
            "storeValues" : "none",
            "trackListPositions" : false
          },
          "c12_0" : {
            "analyzers" : [
              "identity"
           ],
           "fields" : {
           },
           "includeAllFields" : true,
           "storeValues" : "none",
           "trackListPositions" : false
         }
       }
     }
      print(queryOutput)

      if (expected_output === queryOutput){
        print(`ok`)
      }


      // creating testviewV2 allias
      db._createView('testViewV2', 'search-alias', {
        'indexes': [
          {
            'collection': 'c1_0',
            'index': 'inverted'
          },
          {
            'collection': 'c2_0',
            'index': 'inverted'
          },
          {
            'collection': 'c3_insert_0',
            'index': 'inverted'
          },
          {
            'collection': 'c4_update_0',
            'index': 'inverted'
          },
          {
            'collection': 'c5_replace_0',
            'index': 'inverted'
          },
          {
            'collection': 'c6_not_null_0',
            'index': 'inverted'
          },
          {
            'collection': 'c7_hex_0',
            'index': 'inverted'
          },
          {
            'collection': 'c8_overwriteFalse_0',
            'index': 'inverted'
          },
          {
            'collection': 'c9_overwriteTrue_0',
            'index': 'inverted'
          },
          {
            'collection': 'c10_multiple_0',
            'index': 'inverted'
          },
          {
            'collection': 'c11_0',
            'index': 'inverted'
          },
          {
            'collection': 'c12_0',
            'index': 'inverted'
          }
        ]
      })

      //-------------------------------------------------------x-------------------------------------------------------------

      //inserting data to all collection
      let Collection_array = [a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12]
      let docsAsStr = fs.read(`${PWD}/makedata_suites/060_computed_value.json`)

      // this function will read and insert and check all the neccessary data for the respective collection
      Collection_array.forEach(col => {
        col.save(JSON.parse(docsAsStr), { silent: true });

        //this cmd will find one docs from the collection
        let expected_field = col.all().limit(1).toArray()
        print(expected_field);
        // print(expected_field[0].cv_field)
        //checking computed value field exit on the collection's doc
        if (col === a1 || col === a2 || col === a7 || col === a8 || col === a9 || col === a11 || col === a12) {
          if (expected_field[0].cv_field !== null) {
            print(`ok`)
          }
        } else if (col === a3) {
          if (expected_field[0].cv_field_insert !== null) {
            print(`ok`)
          }
        } else if (col === a10) {
          if (expected_field[0].cv_field1 !== null) {
            print(`ok`)
          }
        }else{
          print(`test skipped intentionally!`)
        }
      })

      // let index_output;
      //execute queries which use indexes and verify that the proper amount of docs are returned
      let index_array = [
        `for doc in ${c1} OPTIONS { indexHint : 'inverted', forceIndexHint: true, waitForSync: true } filter doc.cv_field == SOUNDEX('sky') collect with count into c return c`,
        `for doc in ${c1} OPTIONS { indexHint : 'persistent' } filter doc.cv_field == SOUNDEX('sky') collect with count into c return c`,
        `for doc in ${c2} OPTIONS { indexHint : 'inverted', forceIndexHint: true, waitForSync: true } filter doc.cv_field == SOUNDEX('dog') collect with count into c return c`,
        `for doc in ${c2} OPTIONS { indexHint : 'persistent' } filter doc.cv_field == SOUNDEX('dog') collect with count into c return c`,
        `for doc in ${c3_insert} OPTIONS { indexHint : 'inverted', forceIndexHint: true, waitForSync: true } filter doc.cv_field_insert == SOUNDEX('frog') collect with count into c return c`,
        `for doc in ${c3_insert} OPTIONS { indexHint : 'persistent' } filter doc.cv_field_insert == SOUNDEX('frog') collect with count into c return c`,
        `for doc in ${c4_update} OPTIONS { indexHint : 'persistent' } filter doc.cv_field_update == SOUNDEX('beer') collect with count into c return c`,
        `for doc in ${c5_replace} OPTIONS { indexHint : 'persistent' } filter doc.cv_field_replace == SOUNDEX('water') collect with count into c return c`,
        `for doc in ${c6_not_null} OPTIONS { indexHint : 'persistent' } filter has(doc, 'cv_field') == true collect with count into c return c`,
        `for doc in ${c7_hex} OPTIONS { indexHint : 'persistent' } filter doc.cv_field == TO_HEX(doc.name) collect with count into c return c`,
        `for doc in ${c8_overwriteFalse} OPTIONS { indexHint : 'persistent' } filter doc.cv_field == CONCAT('42_', TO_STRING(doc.field)) collect with count into c return c`,
        `for doc in ${c9_overwriteTrue} OPTIONS { indexHint : 'persistent' } filter doc.cv_field == CONCAT('42_', TO_STRING(doc.field)) collect with count into c return c`,
        `for doc in ${c10_multiple} OPTIONS { indexHint : 'persistent' } filter doc.cv_field1 == 'foo' and doc.cv_field2 == 'bar' and doc.cv_field3 == 'baz' collect with count into c return c`,
        `for doc in ${c11} OPTIONS { indexHint : 'persistent' } filter doc.cv_field == CONCAT(doc._key, ' ', doc._id, ' ', doc._rev) collect with count into c return c`,
      ];

      let index_exp_output = [64000, 64000, 64000, 64000, 64000, 64000, 0, 0, 0, 64000, 32000, 64000, 64000, 64000]
      
      let resultComparision = (input_array, output_array) =>{
        for(let i=0; i<input_array.length; i++){
          let output = db._query(input_array[i]).toArray()
          
          if(Number(output) === output_array[i]){
            print('ok')
          }else{
            throw new Error(`Index query ${output} didn't match with ${output_array[i]}!`);
          }
        }
      }

      resultComparision(index_array, index_exp_output)

      //execute queries which use views and verify that the proper amount of docs are returned
      // let views_output;
      let views_array = [
        `for doc in testView search doc.cv_field == SOUNDEX('sky') collect with count into c return c`,
        `for doc in testView search doc.cv_field == SOUNDEX('dog') collect with count into c return c`,
        `for doc in testView search doc.cv_field_insert == SOUNDEX('frog') collect with count into c return c`,
        `for doc in testView search doc.cv_field_update == SOUNDEX('beer') collect with count into c return c`,
        `for doc in testView search doc.cv_field_replace == SOUNDEX('water') collect with count into c return c`,
        `for doc in testView filter doc.cv_field == to_hex(doc.name) collect with count into c return c`,
        `for doc in testView filter doc.cv_field == CONCAT('42_', TO_STRING(doc.field)) collect with count into c return c`,
        `for doc in testView search doc.cv_field1=='foo' and doc.cv_field2=='bar' and doc.cv_field3=='baz' collect with count into c return c`,
        `for doc in testView filter doc.cv_field == CONCAT(doc._key, ' ', doc._id, ' ', doc._rev) collect with count into c return c`,
        `for doc in testViewV2 search doc.cv_field == SOUNDEX('sky') collect with count into c return c`, 
        `for doc in testViewV2 search doc.cv_field == SOUNDEX('dog') collect with count into c return c`,
        `for doc in testViewV2 search doc.cv_field_insert == SOUNDEX('frog') collect with count into c return c`,
        `for doc in testViewV2 search doc.cv_field_update == SOUNDEX('beer') collect with count into c return c`,
        `for doc in testViewV2 search doc.cv_field_replace == SOUNDEX('water') collect with count into c return c`,
        `for doc in testViewV2 search doc.cv_field == null collect with count into c return c`,
        `for doc in testViewV2 filter doc.cv_field == to_hex(doc.name) collect with count into c return c`,
        `for doc in testViewV2 filter doc.cv_field == CONCAT('42_', TO_STRING(doc.field)) collect with count into c return c`,
        `for doc in testViewV2 search doc.cv_field1=='foo' and doc.cv_field2=='bar' and doc.cv_field3=='baz' collect with count into c return c`,
        `for doc in testViewV2 filter doc.cv_field == CONCAT(doc._key, ' ', doc._id, ' ', doc._rev) collect with count into c return c`
      ]

      let views_exp_output = [64000, 64000, 64000, 0, 0, 64000, 96000, 64000, 64000, 64000, 64000, 64000, 0, 0, 160000, 64000, 96000, 64000, 64000]

      resultComparision(views_array, views_exp_output)

      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      print(`checking data ${dbCount}`);
      return 0;
    },
    clearDataDB: function (options, isCluster, isEnterprise, dbCount, database) {
      print(`checking data ${dbCount}`);
      let c1 = `c1_${dbCount}`;
      let c2 = `c2_${dbCount}`;
      let c3_insert = `c3_insert_${dbCount}`;
      let c4_update = `c4_update_${dbCount}`;
      let c5_replace = `c5_replace_${dbCount}`;
      let c6_not_null = `c6_not_null_${dbCount}`;
      let c7_hex = `c7_hex_${dbCount}`;
      let c8_overwriteFalse = `c8_overwriteFalse_${dbCount}`;
      let c9_overwriteTrue = `c9_overwriteTrue_${dbCount}`;
      let c10_multiple = `c10_multiple_${dbCount}`;
      let c11 = `c11_${dbCount}`;
      let c12 = `c12_${dbCount}`;

      Collection_array = [c1, c2, c3_insert, c4_update, c5_replace, c6_not_null, c7_hex, c8_overwriteFalse, c9_overwriteTrue, c10_multiple, c11, c12]

      Collection_array.forEach(col => {
        db.col.properties({computedValues: []})
        //checking the properties set to null properly
        if(db.col.properties()["computedValues"] === null){
          print('ok')
          //drop the collection after check
          db._drop(col);
          progress(`deleting ${col} collection`);
        }else{
          throw new Error(`${col} deletion failed!`);
        }
        
      })
      

      return 0;
    }
  };

}());