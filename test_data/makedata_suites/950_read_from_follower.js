/* global print, assertTrue, assertFalse, assertEqual */
const jsunity = require('jsunity');

const testCollName = "ReadFromFollowerCollection";
const httpGetMetric = "arangodb_http_request_statistics_http_get_requests_total";
const httpPutMetric = "arangodb_http_request_statistics_http_put_requests_total";

const RED = require('internal').COLORS.COLOR_RED;
const RESET = require('internal').COLORS.COLOR_RESET;
let instanceInfo = null;
const wait = require("internal").wait;

const nrTries = 1000;

getRawMetric = function (instance, user, tags) {
  let ex;
  let sleepTime = 0.1;
  opts = { "jwt": instance.JWT_header };
  do {
    try {
      resp = download(instance.url + '/_admin/metrics' + tags, '', opts);
      if (resp.code !== 200) {
        throw "Error fetching metric. Server response:\n" + JSON.stringify(resp);
      } else {
        return resp;
      }
    } catch (e) {
      ex = e;
      print(RED + "connecting to " + instance.url + " failed - retrying (" + ex + ")" + RESET);
    }
    sleepTime *= 2;
    sleep(sleepTime);
  } while (sleepTime < 5);
  print(RED + "giving up!" + RESET);
  throw ex;
};

getAllMetric = function (instance, user, tags) {
  let res = getRawMetric(instance, user, tags);
  return res.body;
};

function getMetricName(text, name) {
  let re = new RegExp("^" + name);
  let matches = text.split('\n').filter((line) => !line.match(/^#/)).filter((line) => line.match(re));
  if (!matches.length) {
    throw "Metric " + name + " not found";
  }
  return Number(matches[0].replace(/^.*{.*}([0-9.]+)$/, "$1"));
}

getMetricFromInstance = function (instance, name) {
  let text = getAllMetric(instance, 'root', '');
  return getMetricName(text, name);
};

getMetric = getMetricFromInstance;

function getMetricName(text, name) {
  let re = new RegExp("^" + name);
  let matches = text.split('\n').filter((line) => !line.match(/^#/)).filter((line) => line.match(re));
  if (!matches.length) {
    throw "Metric " + name + " not found";
  }
  return Number(matches[0].replace(/^.*{.*}([0-9.]+)$/, "$1"));
}

function getMetricsForCollections(cols) {
  cols.forEach(colName => {
    // Collect some information and move shards:
    coll = db._collection(collName);
    shards = coll.shards(true);
    shardId = Object.keys(shards)[0];
    leader = getEndpointById(shards[shardId][0]);
    follower = getEndpointById(shards[shardId][1]);

  });
};

getEndpointById = function (id) {
  for (instance of instanceInfo["arangods"]) {
    if (instance['id'] === id) {
      return instance['url'];
    }
  }
  throw "Can't find endpoint for this uuid: " + id;
};

getInstanceById = function (id) {
  for (instance of instanceInfo["arangods"]) {
    if (instance['id'] === id) {
      return instance;
    }
  }
  throw "Can't find instance with such uuid: " + id;
};

moveShard = function (database, collection, shard, fromServer, toServer, dontwait, expectedResult) {
  let body = { database, collection, shard, fromServer, toServer };
  let result = db._connection.POST("/_admin/cluster/moveShard", body);
  if (dontwait) {
    return result;
  }
  // Now wait until the job we triggered is finished:
  var count = 600;   // seconds
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
    print(".");
  }
};

(function () {
  return {
    isSupported: function (version, oldVersion, options, enterprise, cluster) {
      // OldVersion is optional and used in case of upgrade.
      // It resembles the version we are upgrading from
      // Current is the version of the database we are attached to
      if (oldVersion === "") {
        oldVersion = currentVersion;
      }
      let old = semver.parse(semver.coerce(oldVersion));
      return enterprise && cluster && semver.gte(old, "3.10.0");
    },

    makeData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
      try {
        db._drop(testCollName);
      } catch (e) { }
      // Create collections:
      let coll = db._create(testCollName, { numberOfShards: 1, replicationFactor: 2, writeConcern: 2 });

      // Insert some data:
      let l = [];
      for (let i = 0; i < 1000; ++i) {
        l.push({ _key: "K" + i, Hallo: i });
      }
      coll.insert(l);
    },

    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      loopCount = 0;

      print('asontehusaonteuhsanoetuhasoentuh');
      let ret = arango.POST('/_db/_system/_api/cursor', {
        query: `FOR x IN cunique_0 RETURN x`
      },
        { 'x-arango-allow-dirty-read': true });

      // check per DB

      // set up test cases
      instanceInfo = JSON.parse(require('internal').env.INSTANCEINFO);

      let ReadFromFollowerTestSuite = function (collName) {
        return function ReadFromFollowerTestSuite() {
          checkReadDistribution = function (readsOnLeader, readsOnFollower, expectedTotalReadCount, expectedLeaderShare, tolerance) {
            leaderMaxValue = expectedTotalReadCount * expectedLeaderShare + expectedTotalReadCount * tolerance;
            leaderMinValue = expectedTotalReadCount * expectedLeaderShare - expectedTotalReadCount * tolerance;
            followerMaxValue = expectedTotalReadCount * (1 - expectedLeaderShare) + expectedTotalReadCount * tolerance;
            followerMinValue = expectedTotalReadCount * (1 - expectedLeaderShare) - expectedTotalReadCount * tolerance;
            assertTrue(readsOnLeader < leaderMaxValue, `Too many reads on leader (${readsOnLeader})`);
            assertTrue(readsOnLeader > leaderMinValue, `Too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower > followerMinValue, `Too few reads on follower (${readsOnFollower})`);
            assertTrue(readsOnFollower < followerMaxValue, `Too many reads on follower (${readsOnFollower})`);
          };
          let coll;
          let shards;
          let shardId;
          let leader_uuid;
          let follower_uuid;
          let leader;
          let follower;
          let keys;
          return {
            setUpAll: function () {
              print(`Setting up ReadFromFollowerTestSuite for collection \"${collName}\".`);
              coll = db._collection(collName);
              shards = coll.shards(true);
              shardIds = Object.keys(shards);
              numberOfShards = shardIds.length;
              shardId = shardIds[0];
              leader_uuid = shards[shardId][0];
              follower_uuid = shards[shardId][1];
              leader = getInstanceById(leader_uuid);
              follower = getInstanceById(follower_uuid);
              keys = db._query(`for d in ${collName} limit ${nrTries} return d._key`).toArray();
              for (i = 0; i < numberOfShards; ++i) {
                shardId = shardIds[i];
                shard = shards[shardId];
                this_leader_uuid = shard[0];
                this_follower_uuid = shard[1];
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
                  `/_api/document/${collName}/${keys[i % (keys.length - 1)]}`,
                  { "X-Arango-Allow-Dirty-Read": "true" });
                assertFalse(res.error);
                assertEqual("true", res.headers["x-arango-potential-dirty-read"]);
              }
              wait(0.3);   // Give statistics time to process ops, need 250ms

              let readsOnLeader = getMetric(leader, httpGetMetric) - leaderBefore;
              let readsOnFollower = getMetric(follower, httpGetMetric) - followerBefore;
              checkReadDistribution(readsOnLeader, readsOnFollower, nrTries, 0.5, 0.1);
            },

            testBatchDocumentReadsReadFromFollowerJSAPI: function () {
              let leaderBefore = getMetric(leader, httpPutMetric);
              let followerBefore = getMetric(follower, httpPutMetric);

              for (let i = 0; i < nrTries; ++i) {
                let j = (i + 1) % (keys.length - 1);
                db._collection(collName).document([keys[i % (keys.length - 1)], keys[j]], { allowDirtyReads: true });
              }
              wait(0.3);   // Give statistics time to process ops, need 250ms
              let readsOnLeader = getMetric(leader, httpPutMetric) - leaderBefore;
              let readsOnFollower = getMetric(follower, httpPutMetric) - followerBefore;

              checkReadDistribution(readsOnLeader, readsOnFollower, nrTries, 0.5, 0.1);
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
                let d = coll.document(keys[i % (keys.length - 1)]);
                trx.abort();
              }
              wait(0.3);   // Give statistics time to process ops, need 250ms
              let readsOnLeader = getMetric(leader, httpGetMetric) - leaderBefore;
              let readsOnFollower = getMetric(follower, httpGetMetric) - followerBefore;

              checkReadDistribution(readsOnLeader, readsOnFollower, nrTries, 0.5, 0.1);
            },

            testBatchDocumentReadsReadFromFollower: function () {
              let leaderBefore = getMetric(leader, httpPutMetric);
              let followerBefore = getMetric(follower, httpPutMetric);

              for (let i = 0; i < nrTries; ++i) {
                let j = (i + 1) % (keys.length - 1);
                let trx = db._createTransaction({
                  collections: { read: [collName] },
                  allowDirtyReads: true
                });
                let coll = trx.collection(collName);
                let d = coll.document([keys[i % (keys.length - 1)], keys[j]]);
                trx.abort();
              }
              wait(0.3);   // Give statistics time to process ops, need 250ms
              let readsOnLeader = getMetric(leader, httpPutMetric) - leaderBefore;
              let readsOnFollower = getMetric(follower, httpPutMetric) - followerBefore;

              checkReadDistribution(readsOnLeader, readsOnFollower, nrTries, 0.5, 0.1);
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
              wait(0.3);   // Give statistics time to process ops, need 250ms

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
                  { "@coll": collName, l: [keys[0], keys[i % (keys.length - 1)], keys[keys.length - 1]] });
                trx.abort();
              }
              wait(0.3);   // Give statistics time to process ops, need 250ms

              let readsOnLeader = getMetric(leader, httpGetMetric) - leaderBefore;
              let readsOnFollower = getMetric(follower, httpGetMetric) - followerBefore;
              assertTrue(readsOnLeader > 0.2 * 3 * nrTries, `Too few reads on leader (${readsOnLeader})`);
              assertTrue(readsOnFollower > 0.2 * 3 * nrTries, `Too few reads on follower (${readsOnFollower})`);
            },
          };
        };
      }

      let collections = [
        testCollName,
        `c_${loopCount}`,
        `chash_${loopCount}`,
        `cunique_${loopCount}`,
      ];
      failed = []
      for (let collection of collections) {
        jsunity.run(ReadFromFollowerTestSuite(collection));
        result = jsunity.done();
        if (!result.status) {
          failed.push(result);
        }
      }
      if (failed.length > 0) {
        throw "Some tests failed. See output above.";
      }
      return 0;
    },
  };

}());
