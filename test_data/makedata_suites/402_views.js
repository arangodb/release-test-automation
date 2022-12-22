/* global print, progress, createCollectionSafe, db, createSafe  */


(function () {

  let testCases = [
    {
      "collectionName": "no_cache",
      "link": {
        "utilizeCache": false, // This value is for testing purpose. It will be ignored during link creation
        includeAllFields: false,
        storeValues: "none",
        trackListPositions: false,
        fields: {
          animal: {},
          name: {}
        },
        "analyzers": ["AqlAnalyzerHash"]
      }
    },
    {
      "collectionName": "cache_true_top",
      "link": {
        "cache": true,
        "utilizeCache": true, // This value is for testing purpose. It will be ignored during link creation
        includeAllFields: false,
        storeValues: "none",
        trackListPositions: false,
        fields: {
          animal: {},
          name: {}
        },
        "analyzers": ["AqlAnalyzerHash"]
      }
    },
    {
      "collectionName": "cache_false_top",
      "link": {
        "cache": false,
        "utilizeCache": false, // This value is for testing purpose. It will be ignored during link creation
        includeAllFields: false,
        storeValues: "none",
        trackListPositions: false,
        fields: {
          animal: {},
          name: {}
        },
        "analyzers": ["AqlAnalyzerHash"]
      }
    },
    {
      "collectionName": "cache_true_bottom",
      "link": {
        "utilizeCache": true, // This value is for testing purpose. It will be ignored during link creation
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
      }
    },
    {
      "collectionName": "cache_false_bottom",
      "link": {
        "utilizeCache": false, // This value is for testing purpose. It will be ignored during link creation
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
      }
    },
    {
      "collectionName": "cache_true_top_true_bottom",
      "link": {
        "utilizeCache": true, // This value is for testing purpose. It will be ignored during link creation
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
      }
    },
    {
      "collectionName": "cache_true_top_false_bottom",
      "link": {
        "utilizeCache": true, // This value is for testing purpose. It will be ignored during link creation
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
      }
    },
    {
      "collectionName": "cache_false_top_true_bottom",
      "link": {
        "utilizeCache": true, // This value is for testing purpose. It will be ignored during link creation
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
      }
    },
    {
      "collectionName": "cache_false_top_false_bottom",
      "link": {
        "utilizeCache": false, // This value is for testing purpose. It will be ignored during link creation
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
      }
    },
    {
      "collectionName": "cache_top_true_geojson",
      "link": {
        "utilizeCache": true, // This value is for testing purpose. It will be ignored during link creation
        "cache": true,
        includeAllFields: false,
        storeValues: "none",
        trackListPositions: false,
        "fields": {
          "geo_location": {
            "analyzers": ["geo_json"]
          }
        },
        "analyzers": ["AqlAnalyzerHash"]
      }
    },
    {
      "collectionName": "cache_bottom_true_geojson",
      "link": {
        "utilizeCache": true, // This value is for testing purpose. It will be ignored during link creation
        includeAllFields: false,
        storeValues: "none",
        trackListPositions: false,
        "fields": {
          "geo_location": {
            "analyzers": ["geo_json"],
            "cache": true
          }
        },
        "analyzers": ["AqlAnalyzerHash"]
      }
    },
    {
      "collectionName": "cache_top_true_geopoint",
      "link": {
        "utilizeCache": true, // This value is for testing purpose. It will be ignored during link creation
        "cache": true,
        includeAllFields: false,
        storeValues: "none",
        trackListPositions: false,
        "fields": {
          "geo_latlng": {
            "analyzers": ["geo_point"]
          }
        },
        "analyzers": ["AqlAnalyzerHash"]
      }
    },
    {
      "collectionName": "cache_bottom_true_geopoint",
      "link": {
        "utilizeCache": true, // This value is for testing purpose. It will be ignored during link creation
        includeAllFields: false,
        storeValues: "none",
        trackListPositions: false,
        "fields": {
          "geo_latlng": {
            "analyzers": ["geo_point"],
            "cache": true
          }
        },
        "analyzers": ["AqlAnalyzerHash"]
      }
    }
  ];

  let simulateNormalization = function (linkDefinition) {
    // This function will simulate field normalization inside link definition.
    /*
    5 possible cases when we should omit 'cache' value from link definition:
          1) ____                2)  ___
                 ____                  'cache': false
  
  
          3)'cache': false    4) 'cache': false     5) 'cache': true
                  ____               'cache': false         'cache': true
    */
                  // if (result["fields"].hasOwnProperty("animal")) {

    let result = linkDefinition;
    // remove 'cache' values from link definition
    if (result.hasOwnProperty("cache")) {
      if (result["fields"].hasOwnProperty("animal")) {
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
      }
    } else {
      if (result["fields"].hasOwnProperty("animal")) {
        if (result["fields"]["animal"].hasOwnProperty("cache")) {
          if (result["fields"]["animal"]["cache"] == false) {
            delete result["fields"]["animal"]["cache"];
          }
        }
      }
    }

    return result;
  };

  let removeCacheFields = function (linkDefinition) {
    // This function will simulate field normalization when 'cache' field is not supported
    // i.e. it will be simply ommited everywhere

    let result = linkDefinition;
    if (result.hasOwnProperty("cache")) {
      delete result["cache"];
    }
    if (result["fields"].hasOwnProperty("animal")) {
      if (result["fields"]["animal"].hasOwnProperty("cache")) {
        delete result["fields"]["animal"]["cache"];
      }
    }
    return result;
  };

  let compareLinks = function (cacheSizeSupported, linkFromView, expectedRawLink) {

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

  const {
    getMetricValue
  } = require(fs.join(PWD, 'common'));

  let jwt_key = null;

  let generateJWT = function (options) {
    if (jwt_key != null) {
      return;
    }

    let content = `{"username": "root","password": "${options.passvoid}" }`;
    let headers = 'Content-Type: application/json';
    let reply = arango.POST_RAW("/_open/auth", content, headers);
    let obj = reply["parsedBody"];
    jwt_key = obj["jwt"];
  };

  let getRawMetrics = function (tags = "") {
    let headers = {};
    headers['accept'] = 'application/json';
    headers["Authorization"] = `Bearer ${jwt_key}`;
    let reply = arango.GET_RAW(`/_admin/metrics/v2${tags}`, headers);
    return reply;
  };

  let getMetricByName = function (name, tags) {
    let res = getRawMetrics(tags);
    if (res.code !== 200) {
      throw "error fetching metric";
    }
    return getMetricValue(res.body, name);
  };

  let getMetricSingle = function (name) {
    return getMetricByName(name, "");
  };

  let getMetricCluster = function (name) {
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

  let getMetric = function (name, options) {
    generateJWT(options);
    if (isCluster) {
      return getMetricCluster(name);
    } else {
      return getMetricSingle(name);
    }
  };

  let isCacheSizeSupported = function (version) {
    return semver.gte(version, "3.9.5") && semver.neq(version, "3.10.0") && semver.neq(version, "3.10.1");
  };
  return {
    isSupported: function (version, oldVersion, enterprise, cluster) {
      return semver.gte(version, '3.9.5');
    },
    makeData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
      // All items created must contain dbCount and loopCount
      print(`making data ${dbCount} ${loopCount}`);

      // create analyzer with 'norm' feature
      const analyzers = require("@arangodb/analyzers");
      analyzers.save("AqlAnalyzerHash", "aql", { "queryString": "return to_hex(to_string(@param))" }, ["frequency", "norm", "position"])
      analyzers.save("geo_json", "geojson", {}, ["frequency", "norm", "position"]);
      analyzers.save("geo_point", "geopoint", { "latitude": ["lat"], "longitude": ["lng"] }, ["frequency", "norm", "position"]);

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

      if (cacheSizeSupported && isEnterprise) {
        cacheSize = getMetric("arangodb_search_columns_cache_size", options);
        if (cacheSize != 0) {
          throw new Error(`initial cache size is ${cacheSize} (not 0)`);
        }
      }

      testCases.forEach(test => {
        // create collection for each testing link
        let collectionName = `${test["collectionName"]}_${loopCount}`;
        createCollectionSafe(collectionName, 3, 1);
        // insert some test data. Also insert version, on which 'make_data' was called
        db._collection(collectionName).insert([
          { "animal": "cat", "name": "tom", "geo_location": { "type": "Point", "coordinates": [0.937, 50.932] }, "geo_latlng": { "lat": 50.932, "lng": 6.937 } },
          { "animal": "mouse", "name": "jerry", "location": { "type": "Point", "coordinates": [12.7, 3.93] }, "geo_latlng": { "lat": 50.941, "lng": 6.956 } },
          { "animal": "dog", "name": "harry", "location": { "type": "Point", "coordinates": [-6.27, 51.81] }, "geo_latlng": { "lat": 50.932, "lng": 6.962 } },
          { "version": currVersion }
        ]);

        // add links to each created collection one by one
        let meta = {
          links: {}
        };
        meta.links[collectionName] = test["link"];
        viewCache.properties(meta);
        viewNoCache.properties(meta);

        if (cacheSizeSupported) {
          // Should we check that current link will use cache?
          let utilizeCache = test["link"]["utilizeCache"]

          // update cacheSize
          if (isEnterprise) {
            cacheSize = getMetric("arangodb_search_columns_cache_size", options);
            if ((cacheSize <= prevCacheSize) && utilizeCache) {
              throw new Error("new cache size is wrong");
            }
            prevCacheSize = cacheSize;
          }
        }
      });
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);

      let oldVersion = db._query(`for d in version_collection_${loopCount} filter HAS(d, 'version') return d.version`).toArray()[0];
      if (semver.lt(oldVersion, '3.9.5')) {
        // old version doesn't support column cache.
        // MakeData was not called. Nothing to check here.
        return;
      }

      let currVersion = db._version();
      let isCacheSupportedOld = isCacheSizeSupported(oldVersion);
      let isCacheSupported = isCacheSizeSupported(currVersion);

      let viewCache = db._view(`viewCache_${loopCount}`);
      let viewNoCache = db._view(`viewNoCache_${loopCount}`);

      // for 3.10.0 and 3.10.1 we should verify that no cache is present
      if (!isCacheSupported || (!isCacheSupportedOld && isCacheSupported) || !isEnterprise) {
        // we can't see 'cache fields' in current version OR
        // in previous version 'cache' was not supported.
        // So it means that in current version there should be NO 'cache' fields
        if (viewCache.properties()["storedValues"][0].hasOwnProperty("cache")) {
          throw new Error(`viewCache: cache value for storedValues is present! oldVersion:${oldVersion}, newVersion:${currVersion}`);
        }
      } else {
        // current and previous versions are aware of 'cache'. 
        // Check that value is present and equal to value from previous version
        if (viewCache.properties()["storedValues"][0]["cache"] != true) {
          throw new Error("cache value for storedValues is not 'true'!");
        }
      }

      if (viewNoCache.properties()["storedValues"][0].hasOwnProperty("cache")) {
        throw new Error(`viewNoCache: cache value for storedValues is present! oldVersion:${oldVersion}, newVersion:${currVersion}`);
      }

      [viewCache, viewNoCache].forEach(view => {
        let actualLinks = view.properties().links;

        testCases.forEach(test => {
          // get link for each collection
          let collectionName = `${test["collectionName"]}_${loopCount}`;
          let linkFromView = actualLinks[collectionName];
          if (!isCacheSupported || (!isCacheSupportedOld && isCacheSupported) || !isEnterprise) {
            // we can't see 'cache fields' in current version OR
            // in previous version 'cache' was not supported.
            // So it means that in current version there should be NO 'cache' fields
            if (linkFromView.hasOwnProperty('cache')) {
              throw new Error(`cache value on root level should not present! oldVersion:${oldVersion}, newVersion:${currVersion}`);
            }
            if (linkFromView["fields"].hasOwnProperty("animal")) {
              if (linkFromView["fields"]["animal"].hasOwnProperty('cache')) {
                throw new Error(`cache value on field level should not present! oldVersion:${oldVersion}, newVersion:${currVersion}`);
              }
            }
            if (linkFromView["fields"].hasOwnProperty("geo_location")) {
              if (linkFromView["fields"]["geo_location"].hasOwnProperty('cache')) {
                throw new Error(`cache value on field level should not present! oldVersion:${oldVersion}, newVersion:${currVersion}`);
              }
            }
            if (linkFromView["fields"].hasOwnProperty("geo_latlng")) {
              if (linkFromView["fields"]["geo_latlng"].hasOwnProperty('cache')) {
                throw new Error(`cache value on field level should not present! oldVersion:${oldVersion}, newVersion:${currVersion}`);
              }
            }
          } else {
            // current and previous versions are aware of 'cache'. 
            // Check that value is present and equal to value from previous version
            let expectedLink = test["link"];
            if (!compareLinks(isCacheSupported, linkFromView, expectedLink)) {
              let msg = `View: ${view.name()}: Links for collection ${collectionName} are not equal! 
              Link from view: ${JSON.stringify(linkFromView)}, Expected link: ${JSON.stringify(expectedLink)}`
              throw new Error(msg);
            }
          }
        });

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
        testCases.forEach(test => {
          // get link for each collection
          let collectionName = `${test["collectionName"]}_${loopCount}`;
          db._drop(collectionName);
        });
      } catch (e) {
        print(e);
      }
      progress();
    }
  };
}());
