/* global print */

function getMetricName(text, name) {
  let re = new RegExp("^" + name);
  let matches = text.split('\n').filter((line) => !line.match(/^#/)).filter((line) => line.match(re));
  if (!matches.length) {
    throw "Metric " + name + " not found";
  }
  return Number(matches[0].replace(/^.*{.*}([0-9.]+)$/, "$1"));
}

exports.getMetric = function (endpoint, name) {
  let text = exports.getAllMetric(endpoint, '');
  return getMetricName(text, name);
};

exports.getMetricSingle = function (name) {
  let res = arango.GET_RAW("/_admin/metrics");
  if (res.code !== 200) {
    throw "error fetching metric";
  }
  return getMetricName(res.body, name);
};


(function () {
  return {
    isSupported: function (version, oldVersion, options, enterprise, cluster) {
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
      // check per DB
      return 0;
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
    }
  };

}());
