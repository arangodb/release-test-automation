/* global print, ARGUMENTS */
//
// Use like this:
//   arangosh USUAL_OPTIONS_INCLUDING_AUTHENTICATION --javascript.execute cleardata.js [DATABASENAME]
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
// `--disabledDbserverUUID      this server is offline, wait for shards on it to be moved
// `--readonly                  the SUT is readonly. fail if writing is successfull.
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

let PWDRE = /.*at (.*)checkdata.js.*/;
let stack = new Error().stack;
let PWD = fs.makeAbsolute(PWDRE.exec(stack)[1]);
let isCluster = arango.GET("/_admin/server/role").role === "COORDINATOR";
let database = "_system";
let databaseName;
let v = db._version(true);
const enterprise = v.license === "enterprise";

const optionsDefaults = {
  disabledDbserverUUID: "",
  minReplicationFactor: 1,
  maxReplicationFactor: 2,
  readonly: false,
  numberOfDBs: 1,
  countOffset: 0,
  dataMultiplier: 1,
  collectionMultiplier: 1,
  collectionCountOffset: 0,
  testFoxx: true,
  singleShard: false,
  progress: false,
  oldVersion: "3.5.0"
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

let CheckDataFuncs = [];
let CheckDataDbFuncs = [];
function scanTestPaths (options) {
  let suites = _.filter(
    fs.list(fs.join(PWD, 'makedata_suites')),
    function (p) {
      return (p.substr(-3) === '.js');
    }).map(function (x) {
      return fs.join(fs.join(PWD, 'makedata_suites'), x);
    }).sort();
  suites.forEach(suitePath => {
    let supported = "";
    let unsupported = "";
    let suite = require("internal").load(suitePath);
    if (suite.isSupported(dbVersion, options.oldVersion, options, enterprise, isCluster)) {
      if ('checkData' in suite) {
        supported += "L" ;
        CheckDataFuncs.push(suite.checkData);
      } else {
        unsupported += " ";
      }
      if ('checkDataDB' in suite) {
        supported += "D";
        CheckDataDbFuncs.push(suite.checkDataDB);
      } else {
        unsupported += " ";
      }
    } else {
      supported = " ";
      unsupported = " ";
    }
    print("[" + supported +"]   " + unsupported + suitePath);
  });
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

scanTestPaths(options);
let dbCount = 0;
while (dbCount < options.numberOfDBs) {
  tStart = time();
  timeLine = [tStart];
  db._useDatabase("_system");

  CheckDataDbFuncs.forEach(func => {
    db._useDatabase("_system");
    dbCount += func(options,
                    isCluster,
                    enterprise,
                    database,
                    dbCount,
                    options.readOnly);
  });

  let loopCount = options.collectionCountOffset;
  while (loopCount < options.collectionMultiplier) {
    progress();
    CheckDataFuncs.forEach(func => {
      func(options,
           isCluster,
           enterprise,
           dbCount,
           loopCount);
    });
    loopCount++;
  }

  console.error(timeLine.join());
  dbCount++;
}
