/* global fs, PWD, writeGraphData, getShardCount, getReplicationFactor,  print, progress, db, createSafe, _, semver */

(function () {
  let gsm;
  let vertices = JSON.parse(fs.readFileSync(`${PWD}/makedata_suites/500_550_570_vertices.json`));
  let smartEdges = JSON.parse(fs.readFileSync(`${PWD}/makedata_suites/550_570_edges.json`));

  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      if (enterprise) {
        gsm = require('@arangodb/smart-graph');
      }
      // strip off -nightly etc:
      let ver = semver.parse(oldVersion.split('-')[0]);
      // as of 3.10 BTS-776 has to have this workaround:
      return enterprise && (cluster || semver.lt(ver, "3.10.0"));
    },
    makeData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
      // All items created must contain dbCount and loopCount
      print(`making data ${dbCount} ${loopCount}`);
      // And now a smart graph (if enterprise):
      createSafe(`G_smart_${loopCount}`, graphName => {
        return gsm._create(graphName,
                           [
                             gsm._relation(`citations_smart_${loopCount}`,
                                           [`patents_smart_${loopCount}`],
                                           [`patents_smart_${loopCount}`])],
                           [],
                           {
                             numberOfShards: getShardCount(3),
                             replicationFactor: getReplicationFactor(2),
                             smartGraphAttribute: "COUNTRY"
                           });
      }, graphName => {
        return gsm._graph(graphName);
      });
      progress('createEGraph2');
      writeGraphData(db._collection(`patents_smart_${loopCount}`),
                     db._collection(`citations_smart_${loopCount}`),
                     _.clone(vertices),
                     _.clone(smartEdges));
      progress('writeEGraph2');
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
      const vColName = `patents_smart_${loopCount}`;
      let patentsSmart = db._collection(vColName);
      if (patentsSmart.count() !== 761) {
        throw new Error(vColName + " expected count to be 761 but is: " + patentsSmart.count());
      }
      progress();
      const eColName = `citations_smart_${loopCount}`;
      let citationsSmart = db._collection(eColName);
      if (citationsSmart.count() !== 1000) {
        throw new Error(eColName + "count expected to be 1000 but is: " + citationsSmart.count());
      }
      progress();
      const gName = `G_smart_${loopCount}`;
      let len = db._query(`FOR v, e, p IN 1..10 OUTBOUND "${patentsSmart.name()}/US:3858245${loopCount}"
                   GRAPH "${gName}"
                   RETURN v`).toArray().length;
      if (len !== 6) {
        throw new Error("Black Currant 6 != " + len);
      }
      progress();
    },
    clearData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
    // Drop graph:
      let gsm = require("@arangodb/smart-graph");
      progress();
      try {
        gsm._drop(`G_smart_${loopCount}`, true);
      } catch (e) { }
    }
  };
}());
