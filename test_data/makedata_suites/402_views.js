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

/*
  5 possible cases when we should omit 'cache' value from link definition:
                      ____                  ___
                        ____                  'cache': false


                      'cache': false        'cache': false      'cache': true
                        ____                  'cache': false       'cache': true
*/

function compareLinks(linkFromView, expectedLink) {
  // remove redundant 'cache': false values from link definition
  if (expectedLink.hasOwnProperty("cache")) {
    if (expectedLink["cache"] == false) {

      if (expectedLink["fields"]["animal"].hasOwnProperty("cache")) {

        if (expectedLink["fields"]["animal"]["cache"] == false) {

          delete expectedLink["cache"];
          delete expectedLink["fields"]["animal"]["cache"];
        } else {
          delete expectedLink["cache"];
        }
      } else {
        delete expectedLink["cache"];
      }
    } else {
      if (expectedLink["fields"]["animal"].hasOwnProperty("cache")) {
        if (expectedLink["fields"]["animal"]["cache"] == true) {
          delete expectedLink["fields"]["animal"]["cache"];
        }
      }
    }
  } else {

    if (expectedLink["fields"]["animal"].hasOwnProperty("cache")) {

      if (expectedLink["fields"]["animal"]["cache"] == false) {

        delete expectedLink["fields"]["animal"]["cache"];
      }
    }
  }

  // remove redundant 'utilizeCache' values
  delete expectedLink["utilizeCache"];

  return _.isEqual(linkFromView, expectedLink);
}

function getMetricName(text, name) {
  let re = new RegExp("^" + name);
  let matches = text.split('\n').filter((line) => !line.match(/^#/)).filter((line) => line.match(re));
  if (!matches.length) {
    throw "Metric " + name + " not found";
  }
  return Number(matches[0].replace(/^.*{.*} ([0-9.]+)$/, "$1"));
}

getMetric = function (endpoint, name) {
  let text = getAllMetric(endpoint, '');
  return getMetricName(text, name);
};

getMetricSingle = function (name) {
  let res = arango.GET_RAW("/_admin/metrics/v2");
  if (res.code !== 200) {
    throw "error fetching metric";
  }
  return getMetricName(res.body, name);
};


(function () {
  return {
    isSupported: function (version, oldVersion, enterprise, cluster) {
      return semver.gte(version, '3.9.5');
    },
    makeData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
      // All items created must contain dbCount and loopCount
      print(`making data ${dbCount} ${loopCount}`);

      print("\n\n\n\nMAKE DATA!!!!\n\n\n\n\n")

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
      let checkCacheSize = (semver.eq(currVersion, "3.9.5") || semver.gte(currVersion, "3.10.2"));

      let cacheSize = 0;
      let prevCacheSize = cacheSize;

      if (checkCacheSize) {
        cacheSize = getMetricSingle("arangodb_search_columns_cache_size");
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

        if (checkCacheSize) {
          // Should we check that current link will use cache?
          let utilizeCache = links[i]["utilizeCache"]

          // update cacheSize
          cacheSize = getMetricSingle("arangodb_search_columns_cache_size");
          // print(cacheSize);
          if ((cacheSize <= prevCacheSize) && utilizeCache) {
            throw new Error("new cache size is wrong");
          }
          prevCacheSize = cacheSize;
        }
      }
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);

      print("\n\n\n\nCHECK DATA!!!!\n\n\n\n\n")

      let currVersion = db._version();
      let checkCache = (semver.eq(currVersion, "3.9.5") || semver.gte(currVersion, "3.10.2"));

      let viewCache = db._view(`viewCache_${loopCount}`);
      let viewNoCache = db._view(`viewNoCache_${loopCount}`);

      if (checkCache) {
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
          if (semver.eq(oldVersion, "3.10.0") || semver.eq(oldVersion, "3.10.1")) {
            if (linkFromView.hasOwnProperty('cache')) {
              throw new Error("cache value on root level should not present!");
            }
            if (linkFromView["fields"]["animal"].hasOwnProperty('cache')) {
              throw new Error("cache value on field level should not present!");
            }
          } else {
            let expectedLink = links[i];
            if (!compareLinks(linkFromView, expectedLink)) {
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
