/* global print, progress, createCollectionSafe, db, createSafe  */

let link_no_cache = {
  "utilizeCache": false, // This value for testing purpose. It will be ignored during link creation
  includeAllFields: false,
  storeValues: "none",
  trackListPositions: false,
  fields: {
    animal: {},
    name: {}
  },
  "analyzers": ["AqlAnalyzerHash"]
};

let link_cache_true_top = {
  "cache": true,
  "utilizeCache": true, // This value for testing purpose. It will be ignored during link creation
  includeAllFields: false,
  storeValues: "none",
  trackListPositions: false,
  fields: {
    animal: {},
    name: {}
  },
  "analyzers": ["AqlAnalyzerHash"]
};

let link_cache_false_top = {
  "cache": false,
  "utilizeCache": false, // This value for testing purpose. It will be ignored during link creation
  includeAllFields: false,
  storeValues: "none",
  trackListPositions: false,
  fields: {
    animal: {},
    name: {}
  },
  "analyzers": ["AqlAnalyzerHash"]
};

let link_cache_true_bottom = {
  "utilizeCache": true, // This value for testing purpose. It will be ignored during link creation
  includeAllFields: false,
  storeValues: "none",
  trackListPositions: false,
  fields: {
    animal: {
      "cache": true,
    },
    name: {}
  },
  "analyzers": ["AqlAnalyzerHash"]
};

let link_cache_false_bottom = {
  "utilizeCache": false, // This value for testing purpose. It will be ignored during link creation
  includeAllFields: false,
  storeValues: "none",
  trackListPositions: false,
  fields: {
    animal: {
      "cache": false,
    },
    name: {}
  },
  "analyzers": ["AqlAnalyzerHash"]
};

let link_cache_true_top_true_bottom = {
  "utilizeCache": true, // This value for testing purpose. It will be ignored during link creation
  "cache": true,
  includeAllFields: false,
  storeValues: "none",
  trackListPositions: false,
  fields: {
    animal: {
      "cache": true,
    },
    name: {}
  },
  "analyzers": ["AqlAnalyzerHash"]
};

let link_cache_true_top_false_bottom = {
  "utilizeCache": true, // This value for testing purpose. It will be ignored during link creation
  "cache": true,
  includeAllFields: false,
  storeValues: "none",
  trackListPositions: false,
  fields: {
    animal: {
      "cache": false,
    },
    name: {}
  },
  "analyzers": ["AqlAnalyzerHash"]
};

let link_cache_false_top_true_bottom = {
  "utilizeCache": true, // This value for testing purpose. It will be ignored during link creation
  "cache": false,
  includeAllFields: false,
  storeValues: "none",
  trackListPositions: false,
  fields: {
    animal: {
      "cache": true,
    },
    name: {}
  },
  "analyzers": ["AqlAnalyzerHash"]
};

let link_cache_false_top_false_bottom = {
  "utilizeCache": false, // This value for testing purpose. It will be ignored during link creation
  "cache": false,
  includeAllFields: false,
  storeValues: "none",
  trackListPositions: false,
  fields: {
    animal: {
      "cache": false,
    },
    name: {}
  },
  "analyzers": ["AqlAnalyzerHash"]
};

let links = [
  link_no_cache,
  link_cache_true_top,
  link_cache_false_top,
  link_cache_true_bottom,
  link_cache_false_bottom,
  link_cache_true_top_true_bottom,
  link_cache_true_top_false_bottom,
  link_cache_false_top_true_bottom,
  link_cache_false_top_false_bottom
];

function simulateNormalization(linkDefinition) {
  // This function will simulate field normalization inside link definition.
  /*
  5 possible cases when we should omit 'cache' value from link definition:
                      ____                  ___
                        ____                  'cache': false


                      'cache': false        'cache': false      'cache': true
                        ____                  'cache': false       'cache': true
  */

  let result = linkDefinition;
  // remove 'cache' values from link definition
  if (result.hasOwnProperty("cache")) {
    if (result["cache"] == false) {

      if (result["fields"]["animal"].hasOwnProperty("cache")) {

        if (result["fields"]["animal"]["cache"] == false) {

          delete result["cache"];
          delete result["fields"]["animal"]["cache"];
        } else {
          delete result["cache"];
        }
      } else {
        delete result["cache"];
      }
    } else {
      if (result["fields"]["animal"].hasOwnProperty("cache")) {
        if (result["fields"]["animal"]["cache"] == true) {
          delete result["fields"]["animal"]["cache"];
        }
      }
    }
  } else {

    if (result["fields"]["animal"].hasOwnProperty("cache")) {

      if (result["fields"]["animal"]["cache"] == false) {

        delete result["fields"]["animal"]["cache"];
      }
    }
  }

  return result;
};

function removeCacheFields(linkDefinition) {
  // This function will simulate field normalization when 'cache' field is not supported
  // i.e. it will be simply ommited everywhere

  let result = linkDefinition;
  if (result.hasOwnProperty("cache")) {
    delete result["cache"];
  }
  if (result["fields"]["animal"].hasOwnProperty("cache")) {
    delete result["fields"]["animal"]["cache"];
  }

  return result;
};

function compareLinks(cacheSizeSupported, linkFromView, expectedRawLink) {

  let expectedLink;
  if (cacheSizeSupported) {
    expectedLink = simulateNormalization(expectedRawLink);
  } else {
    expectedLink = removeCacheFields(expectedRawLink);
  }

  // remove redundant 'utilizeCache' values. 
  delete expectedLink["utilizeCache"];

  // actual comparison
  return _.isEqual(linkFromView, expectedLink);
};

function getMetricValue(text, name) {
  let re = new RegExp("^" + name);
  let matches = text.split('\n').filter((line) => !line.match(/^#/)).filter((line) => line.match(re));
  if (!matches.length) {
    throw "Metric " + name + " not found";
  }
  return Number(matches[0].replace(/^.*{.*} ([0-9.]+)$/, "$1"));
};

let instanceInfo = null;
let jwt_key = null;

function generateJWT(options) {
  if (jwt_key != null) {
    return;
  }

  let content = `{"username": "root","password": "${options.passvoid}" }`;
  let headers = 'Content-Type: application/json';
  let reply = arango.POST_RAW("/_open/auth", content, headers);
  let obj = reply["parsedBody"];
  jwt_key = obj["jwt"];
};

getRawMetric = function (tags = "") {
  let headers = {};
  headers['accept'] = 'application/json';
  headers["Authorization"] = `Bearer ${jwt_key}`;

  let reply = arango.GET_RAW(`/_admin/metrics/v2${tags}`, headers);
  return reply;
};

getMetricByName = function (name, tags) {
  let res = getRawMetric(tags);
  if (res.code !== 200) {
    throw "error fetching metric";
  }
  return getMetricValue(res.body, name);
};

getMetricSingle = function (name) {
  return getMetricByName(name, "");
};

getMetricCluster = function (name) {
  let headers = {};
  headers['accept'] = 'application/json';
  headers["Authorization"] = `Bearer ${jwt_key}`;
  let clusterHealth = arango.GET_RAW("/_admin/cluster/health", headers)["parsedBody"]["Health"];

  let serversId = [];
  for (let [key, value] of Object.entries(clusterHealth)) {
    if (value.Role.toLowerCase() == "dbserver") {
      serversId.push(key);
    }
  }

  let value = 0;
  for (let i = 0; i < serversId.length; i++) {
    value += getMetricByName(name, `?serverId=${serversId[i]}`);
  }

  return value;
};

getMetric = function (name, options) {
  generateJWT(options);
  if (isCluster) {
    return getMetricCluster(name);
  } else {
    return getMetricSingle(name);
  }
};

isCacheSizeSupported = function (version) {
  return (semver.eq(version, "3.9.5") || semver.gte(version, "3.10.2"));
};

(function () {
  return {
    isSupported: function (version, oldVersion, enterprise, cluster) {
      return semver.gte(version, '3.9.5');
    },
    makeData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
      // All items created must contain dbCount and loopCount
      print(`making data ${dbCount} ${loopCount}`);

      print("\n\n\n\nMAKE DATA!!!!\n\n\n\n\n");

      // create analyzer with 'norm' feature
      analyzers.save("AqlAnalyzerHash", "aql", { queryString: "return to_hex(to_string(@param))" }, ["frequency", "norm", "position"])

      // create views for testing
      progress('createViewCache');
      let viewNameCache = `viewCache_${loopCount}`;
      let viewCache = createSafe(viewNameCache,
        viewNameCache => {
          return db._createView(viewNameCache, "arangosearch", { "storedValues": [{ "fields": ["animal", "name"], "cache": true }] });
        }, viewNameCache => {
          return db._view(viewNameCache);
        }
      );

      progress('createViewNoCache');
      let viewNameNoCache = `viewNoCache_${loopCount}`;
      let viewNoCache = createSafe(viewNameNoCache,
        viewNameNoCache => {
          return db._createView(viewNameNoCache, "arangosearch", { "storedValues": [{ "fields": ["animal", "name"], "cache": false }] });
        }, viewNameNoCache => {
          return db._view(viewNameNoCache);
        }
      );

      let currVersion = db._version();
      let cacheSizeSupported = isCacheSizeSupported(currVersion);

      let cacheSize = 0;
      let prevCacheSize = cacheSize;

      if (cacheSizeSupported) {
        cacheSize = getMetric("arangodb_search_columns_cache_size", options);
        if (cacheSize != 0) {
          throw new Error("initial cache size is not 0");
        }
        prevCacheSize = cacheSize;
      }

      for (let i = 0; i < links.length; i++) {
        // create collection for each testing link
        let collectionName = `collectionCache${i}_${loopCount}`;
        createCollectionSafe(collectionName, 3, 1);
        // insert some test data. Also insert version, on which 'make_data' was called
        db._collection(collectionName).insert([
          { "animal": "cat", "name": "tom" },
          { "animal": "mouse", "name": "jerry" },
          { "animal": "dog", "name": "harry" },
          { "version": currVersion }
        ]);

        // add links to each created collection one by one
        let meta = {
          links: {}
        };
        meta.links[collectionName] = links[i];
        viewCache.properties(meta);
        viewNoCache.properties(meta);

        if (cacheSizeSupported) {
          // Should we check that current link will use cache?
          let utilizeCache = links[i]["utilizeCache"]

          // update cacheSize
          cacheSize = getMetric("arangodb_search_columns_cache_size", options);
          print(cacheSize);
          if ((cacheSize <= prevCacheSize) && utilizeCache) {
            throw new Error("new cache size is wrong");
          }
          prevCacheSize = cacheSize;
        }
      }
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {

      
      print(`checking data ${dbCount} ${loopCount}`);
      
      print("\n\n\n\n\n\n\n\n\n\n\n\nCHECK DATA!!!!\n\n\n\n\n\n\n\n\n\n\n\n\n")

      let currVersion = db._version();
      let isCacheSupported = isCacheSizeSupported(currVersion);

      let viewCache = db._view(`viewCache_${loopCount}`);
      let viewNoCache = db._view(`viewNoCache_${loopCount}`);

      if (isCacheSupported) {
        if (viewCache.properties()["storedValues"][0]["cache"] != true) {
          throw new Error("cache value for storedValues is not true!");
        }
        if (viewNoCache.properties()["storedValues"][0].hasOwnProperty("cache")) {
          throw new Error("cache value for storedValues is present!");
        }
      }

      [viewCache, viewNoCache].forEach(view => {
        let actualLinks = view.properties().links;

        for (let i = 0; i < links.length; i++) {
          // get link for each collection
          let collectionName = `collectionCache${i}_${loopCount}`;
          let linkFromView = actualLinks[collectionName];

          // for 3.10.0 and 3.10.0 we should verify that no cache is present
          let oldVersion = db._query(`for d in ${collectionName} filter HAS(d, 'version') return d.version`).toArray()[0];
          if (!isCacheSizeSupported(oldVersion)) {
            if (linkFromView.hasOwnProperty('cache')) {
              throw new Error("cache value on root level should not present!");
            }
            if (linkFromView["fields"]["animal"].hasOwnProperty('cache')) {
              throw new Error("cache value on field level should not present!");
            }
          } else {
            let expectedLink = links[i];
            if (!compareLinks(isCacheSupported, linkFromView, expectedLink)) {
              throw new Error(`links are not equal! ${linkFromView} ${expectedLink}`)
            }
          }
        }
      });

      progress();
    },

    clearData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);

      try {
        db._dropView(`viewCache_${loopCount}`);
      } catch (e) {
        print(e);
      }
      progress();
      try {
        for (let i = 0; i < links.length; i++) {
          // create collection for each testing link
          let collectionName = `collectionCache${i}_${loopCount}`;
          db._drop(collectionName);
        }
      } catch (e) {
        print(e);
      }
      progress();
    }
  };
}());
