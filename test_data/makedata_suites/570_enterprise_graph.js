/* global fs, PWD, writeGraphData, getShardCount, getReplicationFactor,  print, progress, db, createSafe, _, semver */

(function () {
  let egm;
  let vertices = JSON.parse(fs.readFileSync(`${PWD}/vertices.json`));
  let smartEdges = JSON.parse(fs.readFileSync(`${PWD}/edges.json`));

  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      if (enterprise) {
        egm = require('@arangodb/enterprise-graph');
      }
      // strip off -nightly etc:
      ver = semver.parse(oldVersion.split('-')[0])
      return enterprise && (semver.gte(ver, "3.10.0"));
    },
    makeData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
      // All items created must contain dbCount and loopCount
      print(`making data ${dbCount} ${loopCount}`);
      // And now a enterprise graph (if enterprise):
      createSafe(`G_enterprise_${loopCount}`, graphName => {
        return egm._create(graphName,
                           [
                             {
                                 "collection": `citations_enterprise_${loopCount}`,
                                 "to": [`patents_enterprise_${loopCount}`],
                                 "from": [`patents_enterprise_${loopCount}`]
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
      writeGraphData(db._collection(`patents_enterprise_${loopCount}`),
                     db._collection(`citations_enterprise_${loopCount}`),
                     _.clone(vertices),
                     _.clone(smartEdges));
      progress('writeEGraph2');
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
      const vColName = `patents_enterprise_${loopCount}`;
      let patentsSmart = db._collection(vColName);
      if (patentsSmart.count() !== 761) {
        throw new Error(vColName + " expected count to be 761 but is: " + patentsSmart.count());
      }
      progress();
      const eColName = `citations_enterprise_${loopCount}`;
      let citationsSmart = db._collection(eColName);
      if (citationsSmart.count() !== 1000) {
        throw new Error(eColName + "count expected to be 1000 but is: " + citationsSmart.count());
      }
      {
          progress();
          //traverse enterprise graph
          const gName = `G_enterprise_${loopCount}`;
          let query = `FOR v, e, p IN 1..10 OUTBOUND "${patentsSmart.name()}/US:3858245${loopCount}"
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
                    FOR v, e, p IN 1..10 OUTBOUND "${patentsSmart.name()}/IL:6009552${loopCount}"
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
    },
    clearData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
    // Drop graph:
      let egm = require("@arangodb/enterprise-graph");
      progress();
      try {
        egm._drop(`G_enterprise_${loopCount}`, true);
      } catch (e) { }
    }
  };
}());
