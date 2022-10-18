/* global print */

const collName = "UnitTestDataReadFromFollowersTrx";
const collName2 = "UnitTestDataReadFromFollowersShardedNonStandardTrx";
const httpGetMetric = "arangodb_http_request_statistics_http_get_requests_total";
const httpPutMetric = "arangodb_http_request_statistics_http_put_requests_total";

const RED = require('internal').COLORS.COLOR_RED;
const RESET = require('internal').COLORS.COLOR_RESET;
const instanceInfo = JSON.parse(require('internal').env.INSTANCEINFO);
const wait = require("internal").wait;

const nrTries = 1000;

reconnectRetry = function(endpoint, databaseName, user, passvoid) {
  let sleepTime = 0.1;
  let ex;
  do {
    try {
      arango.reconnect(endpoint, databaseName, user, passvoid);
      return;
    } catch (e) {
      ex = e;
      print(RED + "connecting to " + endpoint + " as user \"" + user + '\"' + ' with password ' +
       '\"' + passvoid + '\"' +" failed - retrying (" + ex.message + ")" + RESET);
    }
    sleepTime *= 2;
    sleep(sleepTime);
  } while (sleepTime < 5);
  print(RED + "giving up!" + RESET);
  throw ex;
};

getRawMetric = function (instance, user, tags) {
  opts = { "jwt": instance.JWT_header };
  resp = download(instance.url + '/_admin/metrics' + tags, '', opts);
  return resp;
};

getAllMetric = function (instance, user, tags) {
  let res = getRawMetric(instance, user, tags);
  if (res.code !== 200) {
    throw "Error fetching metric. Server response:\n" + JSON.stringify(res);
  }
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

getEndpointById = function(id) {
  for (instance of instanceInfo) {
    if (instance['uuid'] === id) {
      return instance['url'];
    }
  }
  throw "Can't find endpoint for this uuid: " + id;
};

getInstanceById = function(id) {
  for (instance of instanceInfo) {
    if (instance['uuid'] === id) {
      return instance;
    }
  }
  throw "Can't find instance with such uuid: " + id;
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
      return  enterprise && cluster && semver.gte(old, "3.10.0");
    },

    makeDataDB: function(options, isCluster, isEnterprise, database, dbCount){
      try {
        db._drop(collName);
        db._drop(collName2);
      } catch(e) {}
      // Create collections:
      let coll = db._create(collName, {numberOfShards: 1, replicationFactor: 2});
      let coll2 = db._create(collName2, {numberOfShards: 2, replicationFactor: 2, shardKeys: ["Hallo"]});

      // Insert some data:
      let l = [];
      let ll = [];
      for (let i = 0; i < 1000; ++i) {
        l.push({_key:"K"+i, Hallo:i});
        ll.push({Hallo:i});
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
                            { 'x-arango-allow-dirty-read': true});

      // check per DB

      // set up test cases
      coll = db._collection(collName);
      shards = coll.shards(true);
      shardId = Object.keys(shards)[0];
      leader = getInstanceById(shards[shardId][0]);
      follower = getInstanceById(shards[shardId][1]);
      {
        //check read from follower feature: basic test case
        let leaderBefore = getMetricFromInstance(leader, httpGetMetric);
        let followerBefore = getMetricFromInstance(follower, httpGetMetric);

        for (let i = 0; i < nrTries; ++i) {
          let trx = db._createTransaction({
            collections: {read: [collName]},
            allowDirtyReads: true});
          let coll = trx.collection(collName);
          let d = coll.document(`K${i % 1000}`);
          trx.abort();
        }
        wait(0.3);   // Give statistics time to process ops, need 250ms
        let readsOnLeader = getMetricFromInstance(leader, httpGetMetric) - leaderBefore;
        let readsOnFollower = getMetricFromInstance(follower, httpGetMetric) - followerBefore;

        assertTrue(readsOnLeader < 0.6 * nrTries, `Too many reads on leader (${readsOnLeader})`);
        assertTrue(readsOnLeader > 0.4 * nrTries, `Too few reads on leader (${readsOnLeader})`);
        assertTrue(readsOnFollower > 0.4 * nrTries, `Too few reads on follower (${readsOnFollower})`);
        assertTrue(readsOnFollower < 0.6 * nrTries, `Too many reads on follower (${readsOnFollower})`);
      }
      return 0;
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
    }
  };

}());
