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
        // documentation link: https://www.arangodb.com/docs/3.9/analyzers.html
  
        print(`making per database data ${dbCount}`);
        
        //creating sample computed values collections
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
  