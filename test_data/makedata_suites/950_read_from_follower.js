/* global print, assertTrue, assertFalse, assertEqual, db, semver, download, sleep, fs, arango, PWD */
const jsunity = require('jsunity');

const testCollName = "ReadFromFollowerCollection";
const httpGetMetric = "arangodb_http_request_statistics_http_get_requests_total";
const httpPutMetric = "arangodb_http_request_statistics_http_put_requests_total";

const RED = require('internal').COLORS.COLOR_RED;
const RESET = require('internal').COLORS.COLOR_RESET;
const wait = require("internal").wait;
let instanceInfo = null;
const nrTries = 1000;
const distributionTolerance = 0.15;

let defaultServerLoggingSettings = [];

const {
  getMetricValue
} = require(fs.join(PWD, 'common'));

let waitForStats = function (instances) {
  outerloop: for (let instance of instances) {
    print("Fetching statistics with the 'sync' flag from the server "
      + instance["name"] + " to force statistics processing.");
    let ex;
    let sleepTime = 0.1;
    let opts = { "jwt": instance.JWT_header };
    do {
      try {
        let resp = download(instance.url + '/_admin/statistics?sync=true', '', opts);
        if (resp.code !== 200) {
          throw "Error fetching statistics with the 'sync' flag. Server response:\n" + JSON.stringify(resp);
        } else {
          continue outerloop;
        }
      } catch (e) {
        let ex = e;
        print(RED + "connecting to " + instance.url + " failed - retrying (" + ex + ")" + RESET);
      }
      sleepTime *= 2;
      sleep(sleepTime);
    } while (sleepTime < 15);
    print(RED + "giving up!" + RESET);
    throw ex;
  }
};

let getRawMetric = function (instance, user, tags) {
  print("Fetching metrics from the server " + instance["name"]);
  let ex;
  let sleepTime = 0.1;
  let opts = { "jwt": instance.JWT_header };
  do {
    try {
      let resp = download(instance.url + '/_admin/metrics' + tags, '', opts);
      if (resp.code !== 200) {
        throw "Error fetching metric. Server response:\n" + JSON.stringify(resp);
      } else {
        return resp;
      }
    } catch (e) {
      let ex = e;
      print(RED + "connecting to " + instance.url + " failed - retrying (" + ex + ")" + RESET);
    }
    sleepTime *= 2;
    sleep(sleepTime);
  } while (sleepTime < 5);
  print(RED + "giving up!" + RESET);
  throw ex;
};

let getAllMetric = function (instance, user, tags) {
  let res = getRawMetric(instance, user, tags);
  return res.body;
};

let getMetricFromInstance = function (instance, name) {
  let text = getAllMetric(instance, 'root', '');
  return getMetricValue(text, name);
};

let getMetric = getMetricFromInstance;

let getInstanceById = function (id) {
  for (let instance of instanceInfo["arangods"]) {
    if (instance['id'] === id) {
      return instance;
    }
  }
  throw "Can't find instance with such uuid: " + id;
};

let moveShard = function (database, collection, shard, fromServer, toServer, dontwait, expectedResult) {
  let body = { database, collection, shard, fromServer, toServer };
  let result = db._connection.POST("/_admin/cluster/moveShard", body);
  if (dontwait) {
    return result;
  }
  // Now wait until the job we triggered is finished:
  var count = 600;   // seconds
  print("Waiting until shard is moved...");
  while (true) {
    var job = db._connection.GET(`/_admin/cluster/queryAgencyJob?id=${result.id}`);
    //console.error("Status of moveShard job:", JSON.stringify(job));
    if (job.error === false && job.status === expectedResult) {
      return result;
    }
    if (count-- < 0) {
      throw "Timeout in waiting for moveShard to complete: " + JSON.stringify(body);
    }
    wait(1.0);
    if (count % 10 === 0) { print("."); };
  }
};

let checkReadDistribution = function (readsOnLeader, readsOnFollower, expectedTotalReadCount, expectedLeaderShare, tolerance) {
  let realTotalReadCount = readsOnLeader + readsOnFollower;
  let maxTotalReadCount = expectedTotalReadCount + expectedTotalReadCount * tolerance;
  let minTotalReadCount = expectedTotalReadCount - expectedTotalReadCount * tolerance;
  let leaderMaxValue = realTotalReadCount * expectedLeaderShare + realTotalReadCount * tolerance;
  let leaderMinValue = realTotalReadCount * expectedLeaderShare - realTotalReadCount * tolerance;
  let followerMaxValue = realTotalReadCount * (1 - expectedLeaderShare) + realTotalReadCount * tolerance;
  let followerMinValue = realTotalReadCount * (1 - expectedLeaderShare) - realTotalReadCount * tolerance;
  let message = ` Expected total reads: ${expectedTotalReadCount}. Real total reads: ${realTotalReadCount}. Reads on leader: ${readsOnLeader}. Reads on follower: ${readsOnFollower}.`;
  assertTrue(realTotalReadCount < maxTotalReadCount, `Too many reads in total. Expected a value between ${minTotalReadCount} and ${maxTotalReadCount}.` + message);
  assertTrue(realTotalReadCount > minTotalReadCount, `Too few reads in total. Expected a value between ${minTotalReadCount} and ${maxTotalReadCount}.` + message);
  assertTrue(readsOnLeader < leaderMaxValue, `Too many reads on leader (${readsOnLeader}). Expected a value between ${leaderMinValue} and ${leaderMaxValue}.` + message);
  assertTrue(readsOnLeader > leaderMinValue, `Too few reads on leader (${readsOnLeader}). Expected a value between ${leaderMinValue} and ${leaderMaxValue}.` + message);
  assertTrue(readsOnFollower > followerMinValue, `Too few reads on follower (${readsOnFollower}). Expected a value between ${followerMinValue} and ${followerMaxValue}.` + message);
  assertTrue(readsOnFollower < followerMaxValue, `Too many reads on follower (${readsOnFollower}). Expected a value between ${followerMinValue} and ${followerMaxValue}.` + message);
};

let setLoggingLevelsForServerById = function (serverId, topic, level) {
  let opts = {};
  opts[topic] = level;
  arango.PUT(`/_admin/log/level?serverId=${serverId}`, opts);
};

let setLoggingForAllServers = function (topic, level) {
  for (let instance of instanceInfo["arangods"]) {
    if (instance["instanceRole"] === "coordinator" || instance["instanceRole"] === "dbserver") {
      let serverId = instance["id"];
      setLoggingLevelsForServerById(serverId, topic, level);
    }
  }
};

let saveServerLoggingSettings = function () {
  defaultServerLoggingSettings = [];
  for (let instance of instanceInfo["arangods"]) {
    if (instance["instanceRole"] === "coordinator" || instance["instanceRole"] === "dbserver") {
      let serverId = instance["id"];
      let loggingInfo = arango.GET(`/_admin/log/level?serverId=${serverId}`);
      defaultServerLoggingSettings.push({ serverId, loggingInfo });
    }
  }
};

let restoreServerLoggingSettings = function (topic) {
  for (let entry of defaultServerLoggingSettings) {
    setLoggingLevelsForServerById(entry["serverId"], topic, entry["loggingInfo"][topic]);
  }
};

(function () {
  let ReadDocsFromFollowerTestSuite = function (collName) {
    return function ReadDocsFromFollowerTestSuite() {
      let coll = null;
      let shards = null;
      let shardId = null;
      let leader_uuid = null;
      let follower_uuid = null;
      let leader = null;
      let follower = null;
      let keys = null;
      return {
        setUpAll: function () {
          print(`Setting up ReadDocsFromFollowerTestSuite for collection \"${collName}\".`);
          instanceInfo = JSON.parse(require('internal').env.INSTANCEINFO);
          coll = db._collection(collName);
          shards = coll.shards(true);
          let shardIds = Object.keys(shards);
          let numberOfShards = shardIds.length;
          shardId = shardIds[0];
          leader_uuid = shards[shardId][0];
          follower_uuid = shards[shardId][1];
          leader = getInstanceById(leader_uuid);
          follower = getInstanceById(follower_uuid);
          keys = db._query(`for d in ${collName} limit ${nrTries} return d._key`).toArray();
          //Move arrange all shards the same way as the first shard: 
          //all shards must have the same leader and follower). 
          for (let i = 1; i < numberOfShards; ++i) {
            //read shard info
            shards = coll.shards(true);
            shardId = shardIds[i];
            let shard = shards[shardId];
            let this_leader_uuid = shard[0];
            let this_follower_uuid = shard[1];
            //move leader
            if (this_leader_uuid !== leader_uuid) {
              moveShard("_system", collName, shardId, this_leader_uuid, leader_uuid, false, "Finished");
            }
            // Now need to wait until we have only 2 replicas again:
            let counter = 60;
            while (true) {
              wait(1.0);
              counter -= 1;
              if (coll.shards(true)[shardId].length === 2) {
                break;
              }
              if (counter <= 0) {
                throw "Timeout waiting for removeFollower job!";
              }
            }
            //update shard info
            shards = coll.shards(true);
            shard = shards[shardId];
            this_leader_uuid = shard[0];
            this_follower_uuid = shard[1];
            //move follower
            if (this_follower_uuid !== follower_uuid) {
              moveShard("_system", collName, shardId, this_follower_uuid, follower_uuid, false, "Finished");
            }
          }
        },
        testSingleDocumentReadsFromFollowers: function () {
          let leaderBefore = getMetric(leader, httpGetMetric);
          let followerBefore = getMetric(follower, httpGetMetric);

          for (let i = 0; i < nrTries; ++i) {
            let res = db._connection.GET_RAW(
              `/_api/document/${collName}/${keys[i % keys.length]}`,
              { "X-Arango-Allow-Dirty-Read": "true" });
            assertFalse(res.error, `Server returned an error. Response: ${JSON.stringify(res)}`);
            assertEqual("true", res.headers["x-arango-potential-dirty-read"],
              "Server response must have header \"x-arango-potential-dirty-read\" value set to true.");
          }
          waitForStats([leader, follower]);

          let readsOnLeader = getMetric(leader, httpGetMetric) - leaderBefore;
          let readsOnFollower = getMetric(follower, httpGetMetric) - followerBefore;
          checkReadDistribution(readsOnLeader, readsOnFollower, nrTries, 0.5, distributionTolerance);
        },

        testBatchDocumentReadsReadFromFollowerJSAPI: function () {
          let leaderBefore = getMetric(leader, httpPutMetric);
          let followerBefore = getMetric(follower, httpPutMetric);

          for (let i = 0; i < nrTries; ++i) {
            let j = (i + 1) % keys.length;
            db._collection(collName).document([keys[i % keys.length], keys[j]], { allowDirtyReads: true });
          }
          waitForStats([leader, follower]);
          let readsOnLeader = getMetric(leader, httpPutMetric) - leaderBefore;
          let readsOnFollower = getMetric(follower, httpPutMetric) - followerBefore;

          checkReadDistribution(readsOnLeader, readsOnFollower, nrTries, 0.5, distributionTolerance);
        },

        testTrxReadFromFollower: function () {
          let leaderBefore = getMetric(leader, httpGetMetric);
          let followerBefore = getMetric(follower, httpGetMetric);

          for (let i = 0; i < nrTries; ++i) {
            let trx = db._createTransaction({
              collections: { read: [collName] },
              allowDirtyReads: true
            });
            let coll = trx.collection(collName);
            let d = coll.document(keys[i % keys.length]);
            trx.abort();
          }
          waitForStats([leader, follower]);
          let readsOnLeader = getMetric(leader, httpGetMetric) - leaderBefore;
          let readsOnFollower = getMetric(follower, httpGetMetric) - followerBefore;

          checkReadDistribution(readsOnLeader, readsOnFollower, nrTries, 0.5, distributionTolerance);
        },

        testBatchDocumentReadsReadFromFollower: function () {
          let leaderBefore = getMetric(leader, httpPutMetric);
          let followerBefore = getMetric(follower, httpPutMetric);

          for (let i = 0; i < nrTries; ++i) {
            let j = (i + 1) % keys.length;
            let trx = db._createTransaction({
              collections: { read: [collName] },
              allowDirtyReads: true
            });
            let coll = trx.collection(collName);
            let d = coll.document([keys[i % keys.length], keys[j]]);
            trx.abort();
          }
          waitForStats([leader, follower]);
          let readsOnLeader = getMetric(leader, httpPutMetric) - leaderBefore;
          let readsOnFollower = getMetric(follower, httpPutMetric) - followerBefore;

          checkReadDistribution(readsOnLeader, readsOnFollower, nrTries, 0.5, distributionTolerance);
        },

        testNormalAQLReadsFromFollowers: function () {
          let leaderBefore = getMetric(leader, httpPutMetric);
          let followerBefore = getMetric(follower, httpPutMetric);

          for (let i = 0; i < nrTries; ++i) {
            let trx = db._createTransaction(
              { collections: { read: [collName] }, allowDirtyReads: true });
            let res = trx.query(
              "FOR d IN @@coll LIMIT 10 RETURN d", { "@coll": collName });
            trx.abort();
          }
          waitForStats([leader, follower]);

          let readsOnLeader = getMetric(leader, httpPutMetric) - leaderBefore;
          let readsOnFollower = getMetric(follower, httpPutMetric) - followerBefore;
          assertTrue(readsOnLeader > 0.2 * nrTries, `Too few reads on leader (${readsOnLeader})`);
          assertTrue(readsOnFollower > 0.2 * nrTries, `Too few reads on follower (${readsOnFollower})`);
        },

        testAQLDOCUMENTReadsFromFollowers: function () {
          let leaderBefore = getMetric(leader, httpGetMetric);
          let followerBefore = getMetric(follower, httpGetMetric);

          for (let i = 0; i < nrTries; ++i) {
            let trx = db._createTransaction(
              { collections: { read: [collName] }, allowDirtyReads: true });
            let res = trx.query(
              "FOR k IN @l RETURN DOCUMENT(@@coll, k)",
              { "@coll": collName, l: [keys[0], keys[i % keys.length], keys[keys.length - 1]] });
            trx.abort();
          }
          waitForStats([leader, follower]);

          let readsOnLeader = getMetric(leader, httpGetMetric) - leaderBefore;
          let readsOnFollower = getMetric(follower, httpGetMetric) - followerBefore;
          assertTrue(readsOnLeader > 0.2 * 3 * nrTries, `Too few reads on leader (${readsOnLeader})`);
          assertTrue(readsOnFollower > 0.2 * 3 * nrTries, `Too few reads on follower (${readsOnFollower})`);
        }
      };
    };
  };
  let ReadCommunityGraphFromFollowerTestSuite = function (collName) {
    return function ReadGraphFromFollowerTestSuite() {
      let coll = null;
      let shards = null;
      let shardId = null;
      let leader_uuid = null;
      let follower_uuid = null;
      let leader = null;
      let follower = null;
      let vertices = [];
      return {
        setUpAll: function () {
          print(`Setting up ReadCommunityGraphFromFollowerTestSuite for collection \"${collName}\".`);
          instanceInfo = JSON.parse(require('internal').env.INSTANCEINFO);
          coll = db._collection(collName);
          shards = coll.shards(true);
          let shardIds = Object.keys(shards);
          let numberOfShards = shardIds.length;
          let shardId = shardIds[0];
          let leader_uuid = shards[shardId][0];
          let follower_uuid = shards[shardId][1];
          leader = getInstanceById(leader_uuid);
          follower = getInstanceById(follower_uuid);
          vertices = vertices.concat(db._query(`for d in ${collName} limit ${nrTries} return d._from`).toArray());
          vertices = vertices.concat(db._query(`for d in ${collName} limit ${nrTries} return d._to`).toArray());
          //Move arrange all shards the same way as the first shard: 
          //all shards must have the same leader and follower). 
          for (let i = 1; i < numberOfShards; ++i) {
            //read shard info
            shards = coll.shards(true);
            shardId = shardIds[i];
            let shard = shards[shardId];
            let this_leader_uuid = shard[0];
            let this_follower_uuid = shard[1];
            //move leader
            if (this_leader_uuid !== leader_uuid) {
              moveShard("_system", collName, shardId, this_leader_uuid, leader_uuid, false, "Finished");
            }
            // Now need to wait until we have only 2 replicas again:
            let counter = 60;
            while (true) {
              wait(1.0);
              counter -= 1;
              if (coll.shards(true)[shardId].length === 2) {
                break;
              }
              if (counter <= 0) {
                throw "Timeout waiting for removeFollower job!";
              }
            }
            //update shard info
            shards = coll.shards(true);
            shard = shards[shardId];
            this_leader_uuid = shard[0];
            this_follower_uuid = shard[1];
            //move follower
            if (this_follower_uuid !== follower_uuid) {
              moveShard("_system", collName, shardId, this_follower_uuid, follower_uuid, false, "Finished");
            }
          }
        },
        testReadEdgesReadsFromFollowers: function () {
          let leaderBefore = getMetric(leader, httpPutMetric);
          let followerBefore = getMetric(follower, httpPutMetric);
          for (let i = 0; i < nrTries; ++i) {
            let res = db._connection.GET_RAW(`/_api/edges/${collName}?vertex=${vertices[i % vertices.length]}`,
              { "X-Arango-Allow-Dirty-Read": "true" });
            assertFalse(res.error, `Server returned an error. Response: ${JSON.stringify(res)}`);
            assertEqual(200, res.code);
            assertEqual("true", res.headers["x-arango-potential-dirty-read"]);
          }
          waitForStats([leader, follower]);

          let readsOnLeader = getMetric(leader, httpPutMetric) - leaderBefore;
          let readsOnFollower = getMetric(follower, httpPutMetric) - followerBefore;

          checkReadDistribution(readsOnLeader, readsOnFollower, readsOnLeader + readsOnFollower, 0.5, distributionTolerance);
        },
      };
    };
  };
  let ReadSmartGraphFromFollowerTestSuite = function (edgeCollName, vertexCollName, databaseName) {
    return function ReadGraphFromFollowerTestSuite() {
      let coll = null;
      let shards = null;
      let shardId = null;
      let leader_uuid = null;
      let follower_uuid = null;
      let leader = null;
      let follower = null;
      let vertices = [];
      return {
        setUpAll: function () {
          print(`Setting up ReadSmartGraphFromFollowerTestSuite for edge collection \"${edgeCollName}\", vertex collection \"${vertexCollName}\".`);
          instanceInfo = JSON.parse(require('internal').env.INSTANCEINFO);
          coll = db._collection(vertexCollName);
          shards = coll.shards(true);
          let shardIds = Object.keys(shards);
          let numberOfShards = shardIds.length;
          shardId = shardIds[0];
          leader_uuid = shards[shardId][0];
          follower_uuid = shards[shardId][1];
          leader = getInstanceById(leader_uuid);
          follower = getInstanceById(follower_uuid);
          vertices = vertices.concat(db._query(`for d in ${edgeCollName} limit ${nrTries} return d._from`).toArray());
          vertices = vertices.concat(db._query(`for d in ${edgeCollName} limit ${nrTries} return d._to`).toArray());
          //Move arrange all shards the same way as the first shard:
          //all shards must have the same leader and follower).
          for (let i = 1; i < numberOfShards; ++i) {
            //read shard info
            shards = coll.shards(true);
            shardId = shardIds[i];
            let shard = shards[shardId];
            let this_leader_uuid = shard[0];
            let this_follower_uuid = shard[1];
            //move leader
            if (this_leader_uuid !== leader_uuid) {
              moveShard(databaseName, vertexCollName, shardId, this_leader_uuid, leader_uuid, false, "Finished");
            }
            // Now need to wait until we have only 2 replicas again:
            let counter = 60;
            while (true) {
              wait(1.0);
              counter -= 1;
              if (coll.shards(true)[shardId].length === 2) {
                break;
              }
              if (counter <= 0) {
                throw "Timeout waiting for removeFollower job!";
              }
            }
            //update shard info
            shards = coll.shards(true);
            shard = shards[shardId];
            this_leader_uuid = shard[0];
            this_follower_uuid = shard[1];
            //move follower
            if (this_follower_uuid !== follower_uuid) {
              moveShard(databaseName, vertexCollName, shardId, this_follower_uuid, follower_uuid, false, "Finished");
            }
          }
        },
        testReadEdgesReadsFromFollowers: function () {
          let leaderBefore = getMetric(leader, httpPutMetric);
          let followerBefore = getMetric(follower, httpPutMetric);
          for (let i = 0; i < nrTries; ++i) {
            let res = db._connection.GET_RAW(`/_api/edges/${edgeCollName}?vertex=${vertices[i % vertices.length]}`,
              { "X-Arango-Allow-Dirty-Read": "true" });
            assertFalse(res.error, "Server response contains an error. Response:\n" + JSON.stringify(res));
            assertEqual(200, res.code);
            assertEqual("true", res.headers["x-arango-potential-dirty-read"]);
          }
          waitForStats([leader, follower]);

          let readsOnLeader = getMetric(leader, httpPutMetric) - leaderBefore;
          let readsOnFollower = getMetric(follower, httpPutMetric) - followerBefore;

          checkReadDistribution(readsOnLeader, readsOnFollower, readsOnLeader + readsOnFollower, 0.5, distributionTolerance);
        },
      };
    };
  };
  return {
    isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
      if (oldVersion === "") {
        oldVersion = currentVersion;
      }
      let old = semver.parse(semver.coerce(oldVersion));
      return enterprise && cluster && semver.gte(old, "3.10.0");
    },

    makeData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
      try {
        db._drop(`${testCollName}_${loopCount}`);
      } catch (e) { }
      // Create collection:
      let coll = db._create(`${testCollName}_${loopCount}`, { numberOfShards: 1, replicationFactor: 2, writeConcern: 2 });

      // Insert some data:
      let l = [];
      for (let i = 0; i < 1000; ++i) {
        l.push({ _key: "K" + i, Hallo: i });
      }
      coll.insert(l);
    },

    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print('asontehusaonteuhsanoetuhasoentuh');
      instanceInfo = JSON.parse(require('internal').env.INSTANCEINFO);
      let failed = [];
      let docCollections = [
        `${testCollName}_${loopCount}`,
        `c_${loopCount}`,
        `chash_${loopCount}`,
        `cunique_${loopCount}`,
      ];
      let graphColls = [
        `citations_naive_${loopCount}`,
        // `citations_smart_${loopCount}`,
      ];
      saveServerLoggingSettings();
      setLoggingForAllServers("requests", "trace");
      for (let collection of docCollections) {
        jsunity.run(ReadDocsFromFollowerTestSuite(collection));
        let result = jsunity.done();
        if (!result.status) {
          failed.push(result);
        }
      }

      jsunity.run(ReadCommunityGraphFromFollowerTestSuite(`citations_naive_${loopCount}`));
      let result = jsunity.done();
      if (!result.status) {
        failed.push(result);
      }

      jsunity.run(ReadSmartGraphFromFollowerTestSuite(`citations_smart_${loopCount}`, `patents_smart_${loopCount}`, "_system"));
      result = jsunity.done();
      if (!result.status) {
        failed.push(result);
      }
      restoreServerLoggingSettings("requests");
      if (failed.length > 0) {
        throw "Some tests failed. See output above.";
      }
      return 0;
    },
    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      //run ReadDocsFromFollowerTestSuite on a one-shard database created in 900_oneshard.js
      instanceInfo = JSON.parse(require('internal').env.INSTANCEINFO);
      let baseName = database;
      if (baseName === "_system") {
        baseName = "system";
      }
      let databaseName = `${baseName}_${dbCount}_oneShard`;
      db._useDatabase(databaseName);
      let failed = [];
      saveServerLoggingSettings();
      setLoggingForAllServers("requests", "trace");
      for (let ccount = 0; ccount < options.collectionMultiplier; ++ccount) {
        let collectionName = `c_${ccount}_0`;
        jsunity.run(ReadDocsFromFollowerTestSuite(collectionName));
        let result = jsunity.done();
        if (!result.status) {
          failed.push(result);
        }
      }

      databaseName = `${baseName}_${dbCount}_entGraph`;
      db._useDatabase(databaseName);
      jsunity.run(ReadSmartGraphFromFollowerTestSuite(`citations_enterprise_${dbCount}`, `patents_enterprise_${dbCount}`, databaseName));
      let result = jsunity.done();
      if (!result.status) {
        failed.push(result);
      }

      db._useDatabase('_system');
      restoreServerLoggingSettings("requests");
      if (failed.length > 0) {
        throw "Some tests failed. See output above.";
      }
      return 0;
    },

    clearData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`clearing data ${dbCount} ${loopCount}`);
      db._drop(`${testCollName}_${loopCount}`, true);
      return 0;
    },
  };

}());
