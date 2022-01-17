/* global print, progress, createCollectionSafe, db, createSafe, semver  */

(function () {
  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      // OldVersion is optional and used in case of upgrade.
      // It resambles the version we are upgradeing from
      // Current is the version of the database we are attached to
      if (oldVersion === "") {
        oldVersion = currentVersion;
      }
      let old = semver.parse(semver.coerce(oldVersion));
      return  enterprise && cluster && semver.gte(old, "3.7.7");
    },
    makeDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      print(`oneShard making per database data ${dbCount}`);
      let baseName = database;
      if (baseName === "_system") {
        baseName = "system";
      }
      progress('Start create OneShard DB');
      db._useDatabase("_system");
      print('#ix');
      const databaseName = `${baseName}_${dbCount}_oneShard`;
      if (db._databases().includes(databaseName)) {
        // its already there - skip this one.
        print(`skipping ${databaseName} - its already there.`);
        return 0;
      }
      const created = createSafe(databaseName,
                                 dbname => {
                                   db._flushCache();
                                   db._createDatabase(dbname, {sharding: "single"});
                                   db._useDatabase(dbname);
                                   return true;
                                 }, dbname => {
                                   db._useDatabase(dbname);
                                   return db._properties().sharding === "single";
                                 }
                                );
      if (!created) {
        // its already wrongly there - skip this one.
        print(`skipping ${databaseName} - it failed to be created, but it is no one-shard.`);
        return 0;
      }
      progress(`created OneShard DB '${databaseName}'`);
      for (let ccount = 0; ccount < options.collectionMultiplier; ++ccount) {
        const c0 = createCollectionSafe(`c_${ccount}_0`, 1, 2);
        const c1 = createCollectionSafe(`c_${ccount}_1`, 1, 2);
        c0.save({
          _key: "knownKey",
          value: "success"
        });
        c1.save({
          _key: "knownKey",
          value: "success"
        });
      }
      db._useDatabase('_system');
      progress('stored OneShard Data');
      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      let baseName = database;
      if (baseName === "_system") {
        baseName = "system";
      }
      progress("Test OneShard setup");
      const databaseName = `${baseName}_${dbCount}_oneShard`;
      print('oneshard vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv ' + databaseName);
      print(db._databases());
      db._useDatabase(databaseName);
      for (let ccount = 0; ccount < options.collectionMultiplier; ++ccount) {
        const query = `
      LET testee = DOCUMENT("c_${ccount}_0/knownKey")
      FOR x IN c_${ccount}_1
        RETURN {v1: testee.value, v2: x.value}
      `;
        const result = db._query(query).toArray();
        if (result.length !== 1 || result[0].v1 !== "success" || result[0].v2 !== "success") {
          throw new Error("DOCUMENT call in OneShard database does not return data");
        }
      }
      db._useDatabase('_system');
      return 0;
    },
    clearDataDB: function (options, isCluster, isEnterprise, dbCount, database) {
      // check per DB
      progress("Test OneShard teardown");
      let baseName = database;
      const databaseName = `${baseName}_${dbCount}_oneShard`;
      db._useDatabase('_system');
      db._dropDatabase(databaseName);

      return 0;
    },
  };
}());
