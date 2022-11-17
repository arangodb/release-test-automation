/* global print, ARGUMENTS */
//
// Use like this:
//   arangosh USUAL_OPTIONS_INCLUDING_AUTHENTICATION --javascript.execute makedata.js [DATABASENAME]
// where DATABASENAME is optional and defaults to "_system". The database
// in question is created (if it is not "_system").
// `--minReplicationFactor [1]  don't create collections with smaller replication factor than this.
// `--maxReplicationFactor [2]  don't create collections with a bigger replication factor than this.
// `--dataMultiplier [1]        0 - no data; else n-times the data
// `--numberOfDBs [1]           count of databases to create and fill
// `--countOffset [0]           number offset at which to start the database count
// `--bigDoc false              attach a big string to the edge documents
// `--collectionMultiplier [1]  how many times to create the collections / index / view / graph set?
// `--collectionCountOffset [0] number offset at which to start the database count
// `--singleShard [false]       whether this should only be a single shard instance
// `--progress [false]          whether to output a keepalive indicator to signal the invoker that work is ongoing
// `--bigDoc                    Increase size of the graph documents
// `--test                      comma separated list of testcases to filter for
'use strict';
const fs = require('fs');
const _ = require('lodash');
const internal = require('internal');
const semver = require('semver');
const arangodb = require("@arangodb");
const console = require("console");
const db = internal.db;
const time = internal.time;
const sleep = internal.sleep;
const ERRORS = arangodb.errors;
let v = db._version(true);
const enterprise = v.license === "enterprise";
const dbVersion = db._version();

let PWDRE = /.*at (.*)makedata.js.*/;
let stack = new Error().stack;
let PWD = fs.makeAbsolute(PWDRE.exec(stack)[1]);
let isCluster = arango.GET("/_admin/server/role").role === "COORDINATOR";
let database = "_system";
let databaseName;
const wantFunctions = ['makeDataDB', 'makeData'];

const {
  scanMakeDataPaths,
  mainTestLoop
} = require(fs.join(PWD, 'common'));

const optionsDefaults = {
  minReplicationFactor: 1,
  maxReplicationFactor: 2,
  numberOfDBs: 1,
  countOffset: 0,
  dataMultiplier: 1,
  collectionMultiplier: 1,
  collectionCountOffset: 0,
  testFoxx: true,
  singleShard: false,
  progress: false,
  newVersion: "3.5.0",
  passvoid: '',
  bigDoc: false,
  test: undefined
};

let args = _.clone(ARGUMENTS);
if ((args.length > 0) &&
    (args[0].slice(0, 1) !== '-')) {
  database = args[0]; // must start with 'system_' else replication fuzzing may delete it!
  args = args.slice(1);
}

let options = internal.parseArgv(args, 0);
_.defaults(options, optionsDefaults);

var numberLength = Math.log(options.numberOfDBs + options.countOffset) * Math.LOG10E + 1 | 0;

const zeroPad = (num) => String(num).padStart(numberLength, '0');

let tStart = 0;
let timeLine = [];
function progress (gaugeName) {
  let now = time();
  let delta = now - tStart;
  timeLine.push(delta);
  if (options.progress) {
    print(`# - ${gaugeName},${tStart},${delta}`);
  }
  tStart = now;
}

function getShardCount (defaultShardCount) {
  if (options.singleShard) {
    return 1;
  }
  return defaultShardCount;
}

function getReplicationFactor (defaultReplicationFactor) {
  if (defaultReplicationFactor > options.maxReplicationFactor) {
    return options.maxReplicationFactor;
  }
  if (defaultReplicationFactor < options.minReplicationFactor) {
    return options.minReplicationFactor;
  }
  return defaultReplicationFactor;
}

let bigDoc = '';
if (options.bigDoc) {
  for (let i = 0; i < 100000; i++) {
    bigDoc += "abcde" + i;
  }
}
function writeGraphData (V, E, vertices, edges) {
  let gcount = 0;
  while (gcount < options.dataMultiplier) {
    edges.forEach(edg => {
      edg._from = V.name() + '/' + edg._from.split('/')[1] + "" + gcount;
      edg._to = V.name() + '/' + edg._to.split('/')[1] + "" + gcount;
      if (options.bigDoc) {
        edg.bigDoc = bigDoc;
      }
    });
    let cVertices = _.clone(vertices);
    cVertices.forEach(vertex => {
      vertex['_key'] = vertex['_key'] + gcount;
    });
    V.insert(vertices);
    E.insert(edges);
    gcount += 1;
  }
}

function createSafe (name, fn1, fnErrorExists) {
  let countDbRetry = 0;
  while (countDbRetry < 50) {
    try {
      return fn1(name);
    } catch (x) {
      if (x.errorNum === ERRORS.ERROR_ARANGO_DUPLICATE_NAME.code) {
        console.error(`${databaseName}: ${name}: its already there? ${x.message} `);
        try {
          // make sure no local caches are there:
          db._flushCache();
          return fnErrorExists(name);
        } catch (x) {
          sleep(countDbRetry * 0.1);
          countDbRetry += 1;
          console.error(`${databaseName}: ${name}: isn't there anyways??? ${x.message} - ${x.stack}`);
        }
      } else {
        sleep(countDbRetry * 0.1);
        countDbRetry += 1;
        console.error(`${databaseName}: ${name}: ${x.message} - ${x.stack}`);
      }
    }
  }
  console.error(`${name}: finally giving up anyways.`);
  throw new Error(`${name} creation failed!`);
}

function createCollectionSafe (name, DefaultNoSharts, DefaultReplFactor) {
  let options = {
    numberOfShards: getShardCount(DefaultNoSharts),
    replicationFactor: getReplicationFactor(DefaultReplFactor)
  };
  return createSafe(name, colName => {
    return db._create(colName, options);
  }, colName => {
    return db._collection(colName);
  });
}

function createIndexSafe (options) {
  let opts = _.clone(options);
  delete opts.col;
  return createSafe(options.col.name(), colname => {
    options.col.ensureIndex(opts);
  }, colName => {
    return false; // well, its there?
  });
}

const fns = scanMakeDataPaths(options, PWD, dbVersion, dbVersion, wantFunctions, 'makeData');
mainTestLoop(options, isCluster, enterprise, fns, function(database) {
  try {
    db._useDatabase("_system");
    db._create('_fishbowl', {
      isSystem: true,
      distributeShardsLike: '_users'
    });
  } catch (err) {}
});
print('YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY');
print(db._databases());
