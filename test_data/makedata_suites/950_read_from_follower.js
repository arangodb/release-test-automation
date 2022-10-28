/* global print, assertTrue, assertFalse, assertEqual */
const jsunity = require('jsunity');

const collName = "UnitTestDataReadFromFollowersTrx";
const collName2 = "UnitTestDataReadFromFollowersShardedNonStandardTrx";
const httpGetMetric = "arangodb_http_request_statistics_http_get_requests_total";
const httpPutMetric = "arangodb_http_request_statistics_http_put_requests_total";

const RED = require('internal').COLORS.COLOR_RED;
const RESET = require('internal').COLORS.COLOR_RESET;
const instanceInfo = JSON.parse(require('internal').env.INSTANCEINFO);
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
  for (instance of instanceInfo) {
    if (instance['uuid'] === id) {
      return instance['url'];
    }
  }
  throw "Can't find endpoint for this uuid: " + id;
};

getInstanceById = function (id) {
  for (instance of instanceInfo) {
    if (instance['uuid'] === id) {
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
      console.error(
        "Timeout in waiting for moveShard to complete: "
        + JSON.stringify(body));
      return false;
    }
    wait(1.0);
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

    makeDataDB: function (options, isCluster, isEnterprise, database, dbCount) {
      try {
        db._drop(collName);
        db._drop(collName2);
      } catch (e) { }
      // Create collections:
      let coll = db._create(collName, { numberOfShards: 1, replicationFactor: 2 });
      let coll2 = db._create(collName2, { numberOfShards: 2, replicationFactor: 2, shardKeys: ["Hallo"] });

      // Insert some data:
      let l = [];
      let ll = [];
      for (let i = 0; i < 1000; ++i) {
        l.push({ _key: "K" + i, Hallo: i });
        ll.push({ Hallo: i });
      }
      coll.insert(l);
      keys = coll2.insert(ll).map(x => x._key);
    },

    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      loopCount = 0;

      print('asontehusaonteuhsanoetuhasoentuh');
      let ret = arango.POST('/_db/_system/_api/cursor', {
        query: `FOR x IN cunique_0 RETURN x`
      },
        { 'x-arango-allow-dirty-read': true });

      // check per DB

      // set up test cases
      coll = db._collection(collName);
      shards = coll.shards(true);
      shardId = Object.keys(shards)[0];
      leader = getInstanceById(shards[shardId][0]);
      follower = getInstanceById(shards[shardId][1]);

      coll2 = db._collection(collName2);
      shards = coll2.shards(true);
      shardIds = Object.keys(shards);
      leaders1 = shards[shardIds[0]][0];
      followers1 = shards[shardIds[0]][1];
      leaders2 = shards[shardIds[1]][0];
      followers2 = shards[shardIds[1]][1];
      let keys = db._query("for d in " + collName2 + " return d._key").toArray();
      if (leaders2 !== leaders1) {
        // Need to move leader for shard2:
        moveShard("_system", collName2, shardIds[1], leaders2, leaders1, false, "Finished");
        // Now need to wait until we have only 2 replicas again:
        let counter = 60;
        while (true) {
          wait(1.0);
          counter -= 1;
          shards = coll2.shards(true);
          if (shards[shardIds[1]].length === 2) {
            break;
          }
          if (counter <= 0) {
            throw "Timeout waiting for removeFollower job!";
          }
        }
        leaders2 = shards[shardIds[1]][0];
        followers2 = shards[shardIds[1]][1];

      }
      if (followers2 !== followers1) {
        // Need to move follower for shard2:
        moveShard("_system", collName2, shardIds[1], followers2, followers1, false, "Finished");
        shards = coll2.shards(true);
        followers2 = shards[shardIds[1]][1];
      }
      leader2 = getInstanceById(leaders1);
      follower2 = getInstanceById(followers1);

      let ReadFromFollowersSuite = function () {
        return {

          testTrxNormal: function () {
            let leaderBefore = getMetric(leader, httpGetMetric);
            let followerBefore = getMetric(follower, httpGetMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction({ collections: { read: [collName] } });
              let coll = trx.collection(collName);
              let d = coll.document(`K${i % 1000}`);
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader, httpGetMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower, httpGetMetric) - followerBefore;

            assertTrue(readsOnLeader > 0.9 * nrTries, `too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower < 0.1 * nrTries, `too many reads on follower (${readsOnFollower})`);
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
              let d = coll.document(`K${i % 1000}`);
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader, httpGetMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower, httpGetMetric) - followerBefore;

            assertTrue(readsOnLeader < 0.6 * nrTries, `Too many reads on leader (${readsOnLeader})`);
            assertTrue(readsOnLeader > 0.4 * nrTries, `Too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower > 0.4 * nrTries, `Too few reads on follower (${readsOnFollower})`);
            assertTrue(readsOnFollower < 0.6 * nrTries, `Too many reads on follower (${readsOnFollower})`);
          },

          testNormalTrxSingleDocumentReadsCustomSharding: function () {
            let leaderBefore = getMetric(leader2, httpGetMetric);
            let followerBefore = getMetric(follower2, httpGetMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction({
                collections: { read: [collName2] }
              });
              let coll = trx.collection(collName2);
              let d = coll.document(`${keys[i % 1000]}`);
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader2, httpGetMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower2, httpGetMetric) - followerBefore;

            assertTrue(readsOnLeader > 0.9 * 2 * nrTries, `too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower < 0.1 * 2 * nrTries, `too many reads on follower (${readsOnFollower})`);
          },

          testTrxSingleDocumentReadsFromFollowersCustomSharding: function () {
            let leaderBefore = getMetric(leader2, httpGetMetric);
            let followerBefore = getMetric(follower2, httpGetMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction({
                collections: { read: [collName2] }, allowDirtyReads: true
              });
              let coll = trx.collection(collName2);
              let d = coll.document(`${keys[i % 1000]}`);
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms

            let readsOnLeader = getMetric(leader2, httpGetMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower2, httpGetMetric) - followerBefore;

            assertTrue(readsOnLeader < 1.2 * nrTries, `Too many reads on leader (${readsOnLeader})`);
            assertTrue(readsOnLeader > 0.8 * nrTries, `Too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower > 0.8 * nrTries, `Too few reads on follower (${readsOnFollower})`);
            assertTrue(readsOnFollower < 1.2 * nrTries, `Too many reads on follower (${readsOnFollower})`);
          },

          testNormalTrxBatchDocumentReads: function () {
            let leaderBefore = getMetric(leader, httpPutMetric);
            let followerBefore = getMetric(follower, httpPutMetric);

            for (let i = 0; i < nrTries; ++i) {
              let j = (i + 1) % 1000;
              let trx = db._createTransaction({ collections: { read: [collName] } });
              let coll = trx.collection(collName);
              let d = coll.document([`K${i % 1000}`, `K${j}`]);
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader, httpPutMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower, httpPutMetric) - followerBefore;

            assertTrue(readsOnLeader > 0.9 * nrTries, `too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower < 0.1 * nrTries, `too many reads on follower (${readsOnFollower})`);
          },

          testBatchDocumentReadsReadFromFollower: function () {
            let leaderBefore = getMetric(leader, httpPutMetric);
            let followerBefore = getMetric(follower, httpPutMetric);

            for (let i = 0; i < nrTries; ++i) {
              let j = (i + 1) % 1000;
              let trx = db._createTransaction({
                collections: { read: [collName] },
                allowDirtyReads: true
              });
              let coll = trx.collection(collName);
              let d = coll.document([`K${i % 1000}`, `K${j}`]);
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader, httpPutMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower, httpPutMetric) - followerBefore;

            assertTrue(readsOnLeader < 0.6 * nrTries, `Too many reads on leader (${readsOnLeader})`);
            assertTrue(readsOnLeader > 0.4 * nrTries, `Too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower > 0.4 * nrTries, `Too few reads on follower (${readsOnFollower})`);
            assertTrue(readsOnFollower < 0.6 * nrTries, `Too many reads on follower (${readsOnFollower})`);
          },

          testNormalBatchDocumentReadsCustomSharding: function () {
            let leaderBefore = getMetric(leader2, httpPutMetric);
            let followerBefore = getMetric(follower2, httpPutMetric);

            for (let i = 0; i < nrTries; ++i) {
              let j = (i + 1) % 1000;
              let trx = db._createTransaction({ collections: { read: [collName2] } });
              let coll = trx.collection(collName2);
              let d = coll.document([`${keys[i % 1000]}`, `${keys[j]}`]);
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader2, httpPutMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower2, httpPutMetric) - followerBefore;

            assertTrue(readsOnLeader > 0.9 * 2 * nrTries, `too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower < 0.1 * 2 * nrTries, `too many reads on follower (${readsOnFollower})`);
          },

          testBatchDocumentReadsReadFromFollowerCustomSharding: function () {
            let leaderBefore = getMetric(leader2, httpPutMetric);
            let followerBefore = getMetric(follower2, httpPutMetric);

            for (let i = 0; i < nrTries; ++i) {
              let j = (i + 1) % 1000;
              let trx = db._createTransaction(
                {
                  collections: { read: [collName2] },
                  allowDirtyReads: true
                });
              let coll = trx.collection(collName2);
              let d = coll.document([`${keys[i % 1000]}`, `${keys[j]}`]);
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader2, httpPutMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower2, httpPutMetric) - followerBefore;

            assertTrue(readsOnLeader < 0.6 * 2 * nrTries, `Too many reads on leader (${readsOnLeader})`);
            assertTrue(readsOnLeader > 0.4 * 2 * nrTries, `Too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower > 0.4 * 2 * nrTries, `Too few reads on follower (${readsOnFollower})`);
            assertTrue(readsOnFollower < 0.6 * 2 * nrTries, `Too many reads on follower (${readsOnFollower})`);
          },

          testNormalAQLReads: function () {
            let leaderBefore = getMetric(leader, httpPutMetric);
            let followerBefore = getMetric(follower, httpPutMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction({ collections: { read: [collName] } });
              let res = trx.query(
                "FOR d IN @@coll LIMIT 10 RETURN d", { "@coll": collName });
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader, httpPutMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower, httpPutMetric) - followerBefore;
            assertTrue(readsOnLeader > 0.9 * nrTries, `too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower < 0.1 * nrTries, `too many reads on follower (${readsOnFollower})`);
          },

          testNormalAQLReadsOption: function () {
            let leaderBefore = getMetric(leader, httpPutMetric);
            let followerBefore = getMetric(follower, httpPutMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction({ collections: { read: [collName] } });
              // The transaction should be stronger here and forbid dirty reads!
              let res = trx.query(
                "FOR d IN @@coll LIMIT 10 RETURN d", { "@coll": collName }, {},
                { allowDirtyReads: true });
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader, httpPutMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower, httpPutMetric) - followerBefore;
            assertTrue(readsOnLeader > 0.9 * nrTries, `too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower < 0.1 * nrTries, `too many reads on follower (${readsOnFollower})`);
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

          testNormalAQLReadsCustomSharding: function () {
            let leaderBefore = getMetric(leader2, httpPutMetric);
            let followerBefore = getMetric(follower2, httpPutMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction({ collections: { read: [collName2] } });
              let res = trx.query(
                "FOR d IN @@coll LIMIT 10 RETURN d", { "@coll": collName2 });
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader2, httpPutMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower2, httpPutMetric) - followerBefore;
            assertTrue(readsOnLeader > 0.9 * nrTries, `too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower < 0.1 * nrTries, `too many reads on follower (${readsOnFollower})`);
          },

          testNormalAQLReadsCustomShardingOption: function () {
            let leaderBefore = getMetric(leader2, httpPutMetric);
            let followerBefore = getMetric(follower2, httpPutMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction({ collections: { read: [collName2] } });
              // The transaction should be stronger and forbid dirty reads!
              let res = trx.query(
                "FOR d IN @@coll LIMIT 10 RETURN d", { "@coll": collName2 }, {},
                { allowDirtyReads: true });
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader2, httpPutMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower2, httpPutMetric) - followerBefore;
            assertTrue(readsOnLeader > 0.9 * nrTries, `too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower < 0.1 * nrTries, `too many reads on follower (${readsOnFollower})`);
          },

          testAQLReadsCustomShardingReadsFromFollowers: function () {
            let leaderBefore = getMetric(leader2, httpPutMetric);
            let followerBefore = getMetric(follower2, httpPutMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction(
                { collections: { read: [collName2] }, allowDirtyReads: true });
              let res = trx.query(
                "FOR d IN @@coll LIMIT 10 RETURN d", { "@coll": collName2 });
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms

            let readsOnLeader = getMetric(leader2, httpPutMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower2, httpPutMetric) - followerBefore;
            assertTrue(readsOnLeader > 2 * 0.2 * nrTries, `Too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower > 2 * 0.2 * nrTries, `Too few reads on follower (${readsOnFollower})`);
          },

          testAQLDOCUMENTReads: function () {
            let leaderBefore = getMetric(leader, httpGetMetric);
            let followerBefore = getMetric(follower, httpGetMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction({ collections: { read: [collName] } });
              let res = trx.query(
                "FOR k IN @l RETURN DOCUMENT(@@coll, k)",
                { "@coll": collName, l: ["K0", "K" + i, "K999"] });
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader, httpGetMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower, httpGetMetric) - followerBefore;
            assertTrue(readsOnLeader > 0.9 * 3 * nrTries, `too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower < 0.1 * 3 * nrTries, `too many reads on follower (${readsOnFollower})`);
          },

          testAQLDOCUMENTReadsOption: function () {
            let leaderBefore = getMetric(leader, httpGetMetric);
            let followerBefore = getMetric(follower, httpGetMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction({ collections: { read: [collName] } });
              // The transaction should be stronger and we should not see dirty reads.
              let res = trx.query(
                "FOR k IN @l RETURN DOCUMENT(@@coll, k)",
                { "@coll": collName, l: ["K0", "K" + i, "K999"] }, {},
                { allowDirtyReads: true });
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader, httpGetMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower, httpGetMetric) - followerBefore;
            assertTrue(readsOnLeader > 0.9 * 3 * nrTries, `too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower < 0.1 * 3 * nrTries, `too many reads on follower (${readsOnFollower})`);
          },

          testAQLDOCUMENTReadsFromFollowers: function () {
            let leaderBefore = getMetric(leader, httpGetMetric);
            let followerBefore = getMetric(follower, httpGetMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction(
                { collections: { read: [collName] }, allowDirtyReads: true });
              let res = trx.query(
                "FOR k IN @l RETURN DOCUMENT(@@coll, k)",
                { "@coll": collName, l: ["K0", "K" + i, "K999"] });
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms

            let readsOnLeader = getMetric(leader, httpGetMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower, httpGetMetric) - followerBefore;
            assertTrue(readsOnLeader > 0.2 * 3 * nrTries, `Too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower > 0.2 * 3 * nrTries, `Too few reads on follower (${readsOnFollower})`);
          },

          testAQLDOCUMENTReadsCustomSharding: function () {
            let leaderBefore = getMetric(leader2, httpGetMetric);
            let followerBefore = getMetric(follower2, httpGetMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction({ collections: { read: [collName2] } });
              let res = trx.query(
                "FOR k IN @l RETURN DOCUMENT(@@coll, k)",
                { "@coll": collName2, l: ["K0", "K" + i, "K999"] });
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader2, httpGetMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower2, httpGetMetric) - followerBefore;
            assertTrue(readsOnLeader > 0.9 * 3 * nrTries, `too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower < 0.1 * 3 * nrTries, `too many reads on follower (${readsOnFollower})`);
          },

          testAQLDOCUMENTReadsCustomShardingOption: function () {
            let leaderBefore = getMetric(leader2, httpGetMetric);
            let followerBefore = getMetric(follower2, httpGetMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction({ collections: { read: [collName2] } });
              let res = trx.query(
                "FOR k IN @l RETURN DOCUMENT(@@coll, k)",
                { "@coll": collName2, l: ["K0", "K" + i, "K999"] }, {},
                { allowDirtyReads: true });
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader2, httpGetMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower2, httpGetMetric) - followerBefore;
            assertTrue(readsOnLeader > 0.9 * 3 * nrTries, `too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower < 0.1 * 3 * nrTries, `too many reads on follower (${readsOnFollower})`);
          },

          testAQLDOCUMENTReadsFromFollowersCustomSharding: function () {
            let leaderBefore = getMetric(leader2, httpGetMetric);
            let followerBefore = getMetric(follower2, httpGetMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction(
                { collections: { read: [collName2] }, allowDirtyReads: true });
              let res = trx.query(
                "FOR k IN @l RETURN DOCUMENT(@@coll, k)",
                { "@coll": collName2, l: ["K0", "K" + i, "K999"] });
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms

            let readsOnLeader = getMetric(leader2, httpGetMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower2, httpGetMetric) - followerBefore;
            assertTrue(readsOnLeader > 0.2 * 3 * nrTries, `Too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower > 0.2 * 3 * nrTries, `Too few reads on follower (${readsOnFollower})`);
          },

          testTrxNormalExists: function () {
            let leaderBefore = getMetric(leader, httpGetMetric);
            let followerBefore = getMetric(follower, httpGetMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction({ collections: { read: [collName] } });
              let coll = trx.collection(collName);
              let d = coll.exists(`K${i % 1000}`);
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader, httpGetMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower, httpGetMetric) - followerBefore;

            assertTrue(readsOnLeader > 0.9 * nrTries, `too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower < 0.1 * nrTries, `too many reads on follower (${readsOnFollower})`);
          },

          testTrxReadFromFollowerExists: function () {
            let leaderBefore = getMetric(leader, httpGetMetric);
            let followerBefore = getMetric(follower, httpGetMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction({
                collections: { read: [collName] },
                allowDirtyReads: true
              });
              let coll = trx.collection(collName);
              let d = coll.exists(`K${i % 1000}`);
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader, httpGetMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower, httpGetMetric) - followerBefore;

            assertTrue(readsOnLeader < 0.6 * nrTries, `Too many reads on leader (${readsOnLeader})`);
            assertTrue(readsOnLeader > 0.4 * nrTries, `Too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower > 0.4 * nrTries, `Too few reads on follower (${readsOnFollower})`);
            assertTrue(readsOnFollower < 0.6 * nrTries, `Too many reads on follower (${readsOnFollower})`);
          },

          testNormalTrxSingleDocumentExistsReadsCustomSharding: function () {
            let leaderBefore = getMetric(leader2, httpGetMetric);
            let followerBefore = getMetric(follower2, httpGetMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction({
                collections: { read: [collName2] }
              });
              let coll = trx.collection(collName2);
              let d = coll.exists(`${keys[i % 1000]}`);
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms
            let readsOnLeader = getMetric(leader2, httpGetMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower2, httpGetMetric) - followerBefore;

            assertTrue(readsOnLeader > 0.9 * 2 * nrTries, `too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower < 0.1 * 2 * nrTries, `too many reads on follower (${readsOnFollower})`);
          },

          testTrxSingleDocumentExistsReadFromFollowersCustomSharding: function () {
            let leaderBefore = getMetric(leader2, httpGetMetric);
            let followerBefore = getMetric(follower2, httpGetMetric);

            for (let i = 0; i < nrTries; ++i) {
              let trx = db._createTransaction({
                collections: { read: [collName2] }, allowDirtyReads: true
              });
              let coll = trx.collection(collName2);
              let d = coll.exists(`${keys[i % 1000]}`);
              trx.abort();
            }
            wait(0.3);   // Give statistics time to process ops, need 250ms

            let readsOnLeader = getMetric(leader2, httpGetMetric) - leaderBefore;
            let readsOnFollower = getMetric(follower2, httpGetMetric) - followerBefore;

            assertTrue(readsOnLeader < 1.2 * nrTries, `Too many reads on leader (${readsOnLeader})`);
            assertTrue(readsOnLeader > 0.8 * nrTries, `Too few reads on leader (${readsOnLeader})`);
            assertTrue(readsOnFollower > 0.8 * nrTries, `Too few reads on follower (${readsOnFollower})`);
            assertTrue(readsOnFollower < 1.2 * nrTries, `Too many reads on follower (${readsOnFollower})`);
          },

        };
      }

      jsunity.run(ReadFromFollowersSuite);
      result = jsunity.done();
      if (!result.status) {
        throw "Some tests failed:\n" + result;
      }
      return 0;
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
    }
  };

}());
