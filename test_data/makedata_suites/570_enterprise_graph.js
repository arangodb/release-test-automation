/* global fs, PWD, writeGraphData, getShardCount, getReplicationFactor,  print, progress, db, createSafe, _, semver */

(function () {
  let egm;
  let vertices = JSON.parse(fs.readFileSync(`${PWD}/makedata_suites/500_550_570_vertices.json`));
  let smartEdges = JSON.parse(fs.readFileSync(`${PWD}/makedata_suites/550_570_edges.json`));

  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      // strip off -nightly etc:
      ver = semver.parse(oldVersion.split('-')[0])
      return enterprise && (semver.gte(ver, "3.10.0"));
    },
    makeDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      egm = require('@arangodb/enterprise-graph');
      // All items created must contain dbCount
      print(`making per database data ${dbCount}`);
      let baseName = database;
      if (baseName === "_system") {
        baseName = "system";
      }
      const databaseName = `${baseName}_${dbCount}_entGraph`;
      const created = createSafe(databaseName,
                                 dbname => {
                                   db._flushCache();
                                   db._createDatabase(dbname);
                                   db._useDatabase(dbname);
                                   return true;
                                 }, dbname => {
                                   throw new Error("Creation of database ${databaseName} failed!");
                                 }
                                );
      progress(`created database '${databaseName}'`);
      createSafe(`G_enterprise_${dbCount}`, graphName => {
        return egm._create(graphName,
                           [
                             {
                                 "collection": `citations_enterprise_${dbCount}`,
                                 "to": [`patents_enterprise_${dbCount}`],
                                 "from": [`patents_enterprise_${dbCount}`]
                              }
                           ],
                           [],
                           {
                             numberOfShards: getShardCount(3),
                             replicationFactor: getReplicationFactor(2),
                             isSmart: true
                           });
      }, graphName => {
        return egm._graph(graphName);
      });
      progress('createEGraph2');
      writeGraphData(db._collection(`patents_enterprise_${dbCount}`),
                     db._collection(`citations_enterprise_${dbCount}`),
                     _.clone(vertices),
                     _.clone(smartEdges));
      progress('writeEGraph2');
      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      print(`checking data in database ${database} dbCount: ${dbCount}`);
      let baseName = database;
      if (baseName === "_system") {
        baseName = "system";
      }
      const databaseName = `${baseName}_${dbCount}_entGraph`;
      db._useDatabase(databaseName);
      const vColName = `patents_enterprise_${dbCount}`;
      let patentsSmart = db._collection(vColName);
      if (patentsSmart.count() !== 761) {
        throw new Error(vColName + " expected count to be 761 but is: " + patentsSmart.count());
      }
      progress();
      const eColName = `citations_enterprise_${dbCount}`;
      let citationsSmart = db._collection(eColName);
      if (citationsSmart.count() !== 1000) {
        throw new Error(eColName + "count expected to be 1000 but is: " + citationsSmart.count());
      }
      {
          progress();
          //traverse enterprise graph
          const gName = `G_enterprise_${dbCount}`;
          let query = `FOR v, e, p IN 1..10 OUTBOUND "${patentsSmart.name()}/US:3858245${dbCount}"
                       GRAPH "${gName}"
                       RETURN v`;
          progress(`running query: ${query}\n`);
          let len = db._query(query).toArray().length;
          if (len !== 6) {
            throw new Error("Black Currant 6 != " + len);
          }
      }
      progress();
      {
          //use enterprise graph's edge collection as an anonymous graph
          let query = `
                    WITH ${patentsSmart.name()}
                    FOR v, e, p IN 1..10 OUTBOUND "${patentsSmart.name()}/IL:6009552${dbCount}"
                    ${citationsSmart.name()}
                    RETURN v
                    `;
          progress(`running query: ${query}\n`);
          let len = db._query(query).toArray().length;
          if (len !== 5) {
            throw new Error("Red Currant 5 != " + len);
          }
      }
      progress();
      return 0;
    },
    clearDataDB: function (options, isCluster, isEnterprise, dbCount, database) {
      print(`Clearing data. Database: ${database}. DBCount: ${dbCount}`);
      let baseName = database;
      if (baseName === "_system") {
        baseName = "system";
      }
      const databaseName = `${baseName}_${dbCount}_entGraph`;
      db._useDatabase(databaseName);
      // Drop graph:
      let egm = require("@arangodb/enterprise-graph");
      progress();
      try {
        egm._drop(`G_enterprise_${dbCount}`, true);
      } catch (e) { }
      return 0;
    }
  };
}());
