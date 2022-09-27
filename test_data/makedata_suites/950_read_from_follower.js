/* global print */

const collName = "UnitTestDataReadFromFollowersTrx";
const collName2 = "UnitTestDataReadFromFollowersShardedNonStandardTrx";
const httpGetMetric = "arangodb_http_request_statistics_http_get_requests_total";
const httpPutMetric = "arangodb_http_request_statistics_http_put_requests_total";
/*
reconnectRetry = function(endpoint, databaseName, user, password) {
  let sleepTime = 0.1;
  let ex;
  do {
    try {
      arango.reconnect(endpoint, databaseName, user, password);
      return;
    } catch (e) {
      ex = e;
      print(RED + "connecting " + endpoint + " failed - retrying (" + ex.message + ")" + RESET);
    }
    sleepTime *= 2;
    sleep(sleepTime);
  } while (sleepTime < 5);
  print(RED + "giving up!" + RESET);
  throw ex;
};

getRawMetric = function (endpoint, tags) {
  const primaryEndpoint = arango.getEndpoint();
  try {
    reconnectRetry(endpoint, db._name(), "root", "");
    return arango.GET_RAW('/_admin/metrics' + tags);
  } finally {
    reconnectRetry(primaryEndpoint, db._name(), "root", "");
  }
};

getAllMetric = function (endpoint, tags) {
  let res = getRawMetric(endpoint, tags);
  if (res.code !== 200) {
    throw "error fetching metric";
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

getMetric = function (endpoint, name) {
  let text = getAllMetric(endpoint, '');
  return getMetricName(text, name);
};

getMetricSingle = function (name) {
  let res = arango.GET_RAW("/_admin/metrics");
  if (res.code !== 200) {
    throw "error fetching metric";
  }
  return getMetricName(res.body, name);
};


function getMetricName(text, name) {
  let re = new RegExp("^" + name);
  let matches = text.split('\n').filter((line) => !line.match(/^#/)).filter((line) => line.match(re));
  if (!matches.length) {
    throw "Metric " + name + " not found";
  }
  return Number(matches[0].replace(/^.*{.*}([0-9.]+)$/, "$1"));
}

getMetric = function (endpoint, name) {
  let text = getAllMetric(endpoint, '');
  return getMetricName(text, name);
};

getMetricSingle = function (name) {
  let res = arango.GET_RAW("/_admin/metrics");
  if (res.code !== 200) {
    throw "error fetching metric";
  }
  return getMetricName(res.body, name);
};
function getMetricsForCollections(cols) {
  cols.forEach(colName => {
    // Collect some information and move shards:
    coll = db._collection(collName);
    shards = coll.shards(true);
    shardId = Object.keys(shards)[0];
    leader = getEndpointById(shards[shardId][0]);
    follower = getEndpointById(shards[shardId][1]);

  });
}
*/

(function () {
  return {
    isSupported: function (version, oldVersion, options, enterprise, cluster) {
      return false;
      print(process.env)
      // OldVersion is optional and used in case of upgrade.
      // It resambles the version we are upgradeing from
      // Current is the version of the database we are attached to
      if (oldVersion === "") {
        oldVersion = currentVersion;
      }
      let old = semver.parse(semver.coerce(oldVersion));
      return  enterprise && cluster && semver.gte(old, "3.10.0");
    },

    checkDataDB: function (options, isCluster, isEnterprise, database, dbCount, readOnly) {
      loopCount = 0;
      // let c = `c_${loopCount}`;
      // print(getMetricsForCollections(c))

      print('asontehusaonteuhsanoetuhasoentuh')
      let ret = arango.POST('/_db/_system/_api/cursor', {
        query: `FOR x IN cunique_0 RETURN x`
      },
                            { 'x-arango-allow-dirty-read': true});
      print(ret)

      // check per DB
      return 0;
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
    }
  };

}());
