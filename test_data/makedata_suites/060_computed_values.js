/* global print, semver, progress, createCollectionSafe, createSafe, db */
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
        print(`making per database data ${dbCount}`);
        
        //creation computed values with sample collections
        let c1 = `c1_${dbCount}`;
        let a1 = createCollectionSafe(c1, 3, 3);
        a1.properties({computedValues: [{"name": "default", "expression": "RETURN SOUNDEX('sky')", overwrite: true}]});

        let c2 = `c2_${dbCount}`;
        let a2 = createCollectionSafe(c2, 3, 3);
        a2.properties({computedValues: [{"name": "default", "expression": "RETURN SOUNDEX('dog')", overwrite: true}]});

        let c3_insert = `c3_insert_${dbCount}`;
        let a3 = createCollectionSafe(c3_insert, 3, 3);
        a3.properties({computedValues: [{"name": "default_insert", "expression": "RETURN SOUNDEX('frog')", computeOn: ["insert"], overwrite: true}]});
        
        let c4_update = `c4_update_${dbCount}`;
        let a4 = createCollectionSafe(c4_update, 3, 3);
        a4.properties({computedValues: [{"name": "default_update", "expression": "RETURN SOUNDEX('beer')", computeOn: ["update"], overwrite: true}]});
        
        let c5_replace = `c5_replace_${dbCount}`;
        let a5 = createCollectionSafe(c5_replace, 3, 3);
        a5.properties({computedValues: [{"name": "default_replace", "expression": "RETURN SOUNDEX('water')", computeOn: ["replace"], overwrite: true}]});
        
        let c6_not_null = `c6_not_null_${dbCount}`;
        let a6 = createCollectionSafe(c6_not_null, 3, 3);
        a6.properties({computedValues: [{"name": "default", "expression": "RETURN null", overwrite: true, keepNull: false}]});

        let c7_hex = `c7_hex_${dbCount}`;
        let a7 = createCollectionSafe(c7_hex, 3, 3);
        a7.properties({computedValues: [{"name": "default", "expression": "RETURN TO_HEX(@doc.name)", overwrite: true}]});

        let c8_overwriteFalse = `c8_overwriteFalse_${dbCount}`;
        let a8 = createCollectionSafe(c8_overwriteFalse, 3, 3);
        a8.properties({computedValues: [{"name": "default", "expression": "RETURN CONCAT('42_', TO_STRING(@doc.field))", overwrite: false}]});

        let c9_overwriteTrue = `c9_overwriteTrue_${dbCount}`;
        let a9 = createCollectionSafe(c9_overwriteTrue, 3, 3);
        a9.properties({computedValues: [{"name": "default", "expression": "RETURN CONCAT('42_', TO_STRING(@doc.field))", overwrite: true}]});

        let c10_multiple = `c10_multiple_${dbCount}`;
        let a10 = createCollectionSafe(c10_multiple, 3, 3);
        a10.properties({computedValues: [{"name": "default1", "expression": "RETURN 'foo'", overwrite: true}, {"name": "default2", "expression": "RETURN 'bar'", overwrite: true}, {"name": "default3", "expression": "RETURN 'baz'", overwrite: true}]});

        let c11 = `c11_${dbCount}`;
        let a11 = createCollectionSafe(c11, 3, 3);
        a11.properties({computedValues: [{"name": "default", "expression": "RETURN CONCAT(@doc._key, ' ', @doc._id, ' ', @doc._rev)", overwrite: true}]});

        let c12 = `c12_${dbCount}`;
        let a12 = createCollectionSafe(c12, 3, 3);
        a12.properties({computedValues: [{"name": "default", "expression": "RETURN [{from_doc: CONCAT(@doc.name, ' ', @doc.field), system:{_key: @doc._key, _rev: @doc._rev, _id: @doc._id}, values: [RANGE(1, 10)]}]", overwrite: true}]});
        
        //-------------------------------------------------------x-------------------------------------------------------------
        
        // this function will check everything regarding given ComVal
        function checkComValProperties(comValueName, obj1, obj2) {
          print(obj1);
          print(obj2);

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
            "name" : "cv_field", 
            "expression" : "RETURN SOUNDEX('sky')", 
            "computeOn" : [ 
              "insert", 
              "update", 
              "replace" 
            ], 
            "overwrite" : true, 
            "failOnWarning" : false, 
            "keepNull" : true 
          } 
        ]
        
        let c1_actual_modification = a1.properties({computedValues: [{"name": "cv_field", "expression": "RETURN SOUNDEX('sky')", overwrite: true}]})
        
        checkComValProperties(c1, c1_exp_modification, c1_actual_modification.computedValues);

        //for c2 comVal
        let c2_exp_modification = [
          { 
            "name" : "default", 
            "expression" : "RETURN SOUNDEX('dog')", 
            "computeOn" : [ 
              "insert", 
              "update", 
              "replace" 
            ], 
            "overwrite" : true, 
            "failOnWarning" : false, 
            "keepNull" : true 
          } 
      
        ]
        
        let c2_actual_modification = a2.properties({computedValues: [{"name": "cv_field", "expression": "RETURN SOUNDEX('dog')", "overwrite": true}]})
        
        checkComValProperties(c2, c2_exp_modification, c2_actual_modification.computedValues);

        //for c3_insert comVal
        let c3_exp_modification = [
          { 
            "name" : "default_insert", 
            "expression" : "RETURN SOUNDEX('frog')", 
            "computeOn" : [ 
              "insert" 
            ], 
            "overwrite" : true, 
            "failOnWarning" : false, 
            "keepNull" : true 
          } 
        ]
        
        let c3_actual_modification = a3.properties({computedValues: [{"name": "cv_field_insert", "expression": "RETURN SOUNDEX('frog')", "computeOn": ["insert"], "overwrite": true}]})
        
        checkComValProperties(c3_insert, c3_exp_modification, c3_actual_modification.computedValues);

        //for c4_update comVal
        let c4_exp_modification = [
          { 
            "name" : "cv_field_update", 
            "expression" : "RETURN SOUNDEX('beer')", 
            "computeOn" : [ 
              "update" 
            ], 
            "overwrite" : true, 
            "failOnWarning" : false, 
            "keepNull" : true 
          }  
        ]
        
        let c4_actual_modification = a4.properties({computedValues: [{"name": "cv_field_update", "expression": "RETURN SOUNDEX('beer')", "computeOn": ["update"], "overwrite": true}]})
        
        checkComValProperties(c4_update, c4_exp_modification, c4_actual_modification.computedValues);

        //for c5_replace comVal
        let c5_exp_modification = [
          { 
            "name" : "cv_field_update", 
            "expression" : "RETURN SOUNDEX('beer')", 
            "computeOn" : [ 
              "update" 
            ], 
            "overwrite" : true, 
            "failOnWarning" : false, 
            "keepNull" : true 
          }  
        ]
        
        let c5_actual_modification = a5.properties({computedValues: [{"name": "cv_field_replace", "expression": "RETURN SOUNDEX('water')", "computeOn": ["replace"], "overwrite": true}]})
        
        checkComValProperties(c5_replace, c5_exp_modification, c5_actual_modification.computedValues);

        //for c6_not_null comVal
        let c6_exp_modification = [
          { 
            "name" : "cv_field", 
            "expression" : "RETURN null", 
            "computeOn" : [ 
              "insert", 
              "update", 
              "replace" 
            ], 
            "overwrite" : true, 
            "failOnWarning" : false, 
            "keepNull" : false 
          }   
        ]
        
        let c6_actual_modification = a6.properties({computedValues: [{"name": "cv_field", "expression": "RETURN null", "overwrite": true, "keepNull": false}]})
        
        checkComValProperties(c6_not_null, c6_exp_modification, c6_actual_modification.computedValues);

        //for c7_hex comVal
        let c7_exp_modification = [
          { 
            "name" : "cv_field", 
            "expression" : "RETURN TO_HEX(@doc.name)", 
            "computeOn" : [ 
              "insert", 
              "update", 
              "replace" 
            ], 
            "overwrite" : true, 
            "failOnWarning" : false, 
            "keepNull" : true 
          }    
        ]
        
        let c7_actual_modification = a7.properties({computedValues: [{"name": "cv_field", "expression": "RETURN TO_HEX(@doc.name)", "overwrite": true}]})
        
        checkComValProperties(c7_hex, c7_exp_modification, c7_actual_modification.computedValues);

        //for c8_overwriteFalse comVal
        let c8_exp_modification = [
          { 
            "name" : "cv_field", 
            "expression" : "RETURN CONCAT('42_', TO_STRING(@doc.field))", 
            "computeOn" : [ 
              "insert", 
              "update", 
              "replace" 
            ], 
            "overwrite" : false, 
            "failOnWarning" : false, 
            "keepNull" : true 
          }   
        ]
        
        let c8_actual_modification = a8.properties({computedValues: [{"name": "cv_field", "expression": "RETURN CONCAT('42_', TO_STRING(@doc.field))", "overwrite": false}]})
        
        checkComValProperties(c8_overwriteFalse, c8_exp_modification, c8_actual_modification.computedValues);

        //for c9_overwriteTrue comVal
        let c9_exp_modification = [
          { 
            "name" : "cv_field", 
            "expression" : "RETURN CONCAT('42_', TO_STRING(@doc.field))", 
            "computeOn" : [ 
              "insert", 
              "update", 
              "replace" 
            ], 
            "overwrite" : false, 
            "failOnWarning" : false, 
            "keepNull" : true 
          }   
        ]
        
        let c9_actual_modification = a9.properties({computedValues: [{"name": "cv_field", "expression": "RETURN CONCAT('42_', TO_STRING(@doc.field))", "overwrite": true}]})
        
        checkComValProperties(c9_overwriteTrue, c9_exp_modification, c9_actual_modification.computedValues);

        //for c10_multiple comVal
        let c10_exp_modification = [
          { 
            "name" : "cv_field1", 
            "expression" : "RETURN 'foo'", 
            "computeOn" : [ 
              "insert", 
              "update", 
              "replace" 
            ], 
            "overwrite" : true, 
            "failOnWarning" : false, 
            "keepNull" : true 
          }, 
          { 
            "name" : "cv_field2", 
            "expression" : "RETURN 'bar'", 
            "computeOn" : [ 
              "insert", 
              "update", 
              "replace" 
            ], 
            "overwrite" : true, 
            "failOnWarning" : false, 
            "keepNull" : true 
          }, 
          { 
            "name" : "cv_field3", 
            "expression" : "RETURN 'baz'", 
            "computeOn" : [ 
              "insert", 
              "update", 
              "replace" 
            ], 
            "overwrite" : true, 
            "failOnWarning" : false, 
            "keepNull" : true 
          }
        ]
        
        let c10_actual_modification = a10.properties({computedValues: [{"name": "cv_field1", "expression": "RETURN 'foo'", "overwrite": true}, {"name": "cv_field2", "expression": "RETURN 'bar'", "overwrite": true}, {"name": "cv_field3", "expression": "RETURN 'baz'", "overwrite": true}]})
        
        checkComValProperties(c10_multiple, c10_exp_modification, c10_actual_modification.computedValues);

        //for c11 comVal
        let c11_exp_modification = [ 
          { 
            "name" : "cv_field", 
            "expression" : "RETURN CONCAT(@doc._key, ' ', @doc._id, ' ', @doc._rev)", 
            "computeOn" : [ 
              "insert", 
              "update", 
              "replace" 
            ], 
            "overwrite" : true, 
            "failOnWarning" : false, 
            "keepNull" : true 
          } 
        ]
        
        let c11_actual_modification = a11.properties({computedValues: [{"name": "cv_field", "expression": "RETURN CONCAT(@doc._key, ' ', @doc._id, ' ', @doc._rev)", "overwrite": true}]})
        
        checkComValProperties(c11, c11_exp_modification, c11_actual_modification.computedValues);

        //for c12_overwriteTrue comVal
        let c12_exp_modification = [
          {
            "name" : "cv_field",
            "expression" : "RETURN CONCAT(@doc._key, ' ', @doc._id, ' ', @doc._rev)",
            "computeOn" : [
              "insert",
              "update",
              "replace"
            ],
            "overwrite" : true,
            "failOnWarning" : false,
            "keepNull" : true
          }    
        ]
        
        let c12_actual_modification = a12.properties({computedValues: [{"name": "cv_field", "expression": "RETURN [{from_doc: CONCAT(@doc.name, ' ', @doc.field), system:{_key: @doc._key, _rev: @doc._rev, _id: @doc._id}, values: [RANGE(1, 10)]}]", "overwrite": true}]})
        
        checkComValProperties(c12, c12_exp_modification, c12_actual_modification.computedValues);



        return 0;
      },
      checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
        print(`checking data ${dbCount}`);
        
        return 0;
      },
      clearDataDB: function (options, isCluster, isEnterprise, dbCount, database) {
        print(`checking data ${dbCount}`);
        
        return 0;
      }
    };
  
  }());
  