/* global arangodb, print,  db, zeroPad, createSafe  */
const ERRORS = arangodb.errors;

(function () {
  return {
    isSupported: function (version, oldVersion, options, enterprise, cluster) {
      return true;
    },

    makeDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      let localCount = 0;
      if (database !== "_system") {
        print('#ix');
        let c = zeroPad(localCount + dbCount + options.countOffset);
        let databaseName = `${database}_${c}`;
        if (db._databases().includes(databaseName)) {
          // its already there - skip this one.
          print(`skipping ${databaseName} - its already there.`);
          localCount++;
          return localCount;
        }
        createSafe(databaseName,
                   dbname => {
                     db._flushCache();
                     db._createDatabase(dbname);
                     return db._useDatabase(dbname);
                   }, dbname => {
                     return db._useDatabase(databaseName);
                   }
                  );
      } else if (options.numberOfDBs > 1) {
        throw new Error("must specify a database prefix if want to work with multiple DBs.");
      }
      return localCount;
    },
    makeData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
      // All items created must contain dbCount and loopCount
      print(`making data ${dbCount} ${loopCount}`);
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      // check per DB
      if (database !== "_system") {
        let c = zeroPad(dbCount + options.countOffset);
        let databaseName = `${database}_${c}`;
        db._useDatabase(databaseName);
      } else if (options.numberOfDBs > 1) {
        throw new Error("must specify a database prefix if want to work with multiple DBs.");
      }
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
      print(`checking data ${dbCount} ${loopCount}`);
    },
    clearDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      if (database !== "_system") {
        let c = zeroPad(dbCount + options.countOffset);
        let databaseName = `${database}_${c}`;
        try {
          db._useDatabase(databaseName);
        } catch (x) {
          if (x.errorNum === ERRORS.ERROR_ARANGO_DATABASE_NOT_FOUND.code) {
            return 1;
          } else {
            print(x);
          }
        }
      } else if (options.numberOfDBs > 1) {
        throw new Error("must specify a database prefix if want to work with multiple DBs.");
      }
      return 0;
    }
  };
}());
