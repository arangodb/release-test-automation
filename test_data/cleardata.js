/* global print, start_pretty_print, ARGUMENTS */

// Use like this:
//   arangosh USUAL_OPTIONS_INCLUDING_AUTHENTICATION --javascript.execute cleardata.js [DATABASENAME]
// where DATABASENAME is optional and defaults to "_system". The database
// in question is dropped (if it is not "_system").

const fs = require('fs');
const _ = require('lodash');
const internal = require('internal')
const arangodb = require("@arangodb");
const semver = require('semver');
const time = internal.time;
const ERRORS = arangodb.errors;
let db = internal.db;
let print = internal.print;
let database = "_system";
let PWDRE = /.*at (.*)cleardata.js.*/;
let stack = new Error().stack;
let isCluster = arango.GET("/_admin/server/role").role === "COORDINATOR";
let PWD = fs.makeAbsolute(PWDRE.exec(stack)[1]);
const dbVersion = db._version();

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
  oldVersion: "3.5.0",
  passvoid: '',
  bigDoc: false,
  passvoid: ''
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
function progress () {
  now = time();
  timeLine.push(now - tStart);
  tStart = now;
  if (options.progress) {
    print("#");
  }
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
let ClearDataFuncs = [];
let ClearDataDbFuncs = [];
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
      if ('clearData' in suite) {
        supported += "L" ;
        ClearDataFuncs.push(suite.clearData);
      } else {
        unsupported += " ";
      }
      if ('clearDataDB' in suite) {
        supported += "D";
        ClearDataDbFuncs.push(suite.clearDataDB);
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

let v = db._connection.GET("/_api/version");
const enterprise = v.license === "enterprise"
scanTestPaths(options);
let dbCount = 0;
while (dbCount < options.numberOfDBs) {
  let databaseName = database
  tStart = time();
  timeLine = [tStart];
  ClearDataDbFuncs.forEach(func => {
    db._useDatabase("_system");
    func(options, isCluster, enterprise, database, dbCount);
  });

  progress();
  loopCount = 0;
  while (loopCount < options.collectionMultiplier) {
    // Drop collections:
    ClearDataFuncs.forEach(func => {
      func(options,
           isCluster,
           enterprise,
           dbCount,
           loopCount);
    });

    progress();
    loopCount ++;
  }
  progress();

  // Drop database:

  if (database != "_system") {
    print('#ix')
    db._useDatabase("_system");

    if (database != "_system") {
      db._dropDatabase(databaseName);
    }
    progress();
  }
  print(timeLine.join());
  dbCount++;
}
