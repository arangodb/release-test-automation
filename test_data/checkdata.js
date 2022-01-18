/* global ARGUMENTS */

// Use like this:
//   arangosh USUAL_OPTIONS_INCLUDING_AUTHENTICATION --javascript.execute checkdata.js [DATABASENAME]
// where DATABASENAME is optional and defaults to "_system".
const internal = require('internal');
const fs = require('fs');
const _ = require('lodash');
const semver = require('semver');

const time = internal.time;
let db = internal.db;
let print = internal.print;
let isCluster = arango.GET("/_admin/server/role").role === "COORDINATOR";
const dbVersion = db._version();

let PWDRE = /.*at (.*)checkdata.js.*/;
let stack = new Error().stack;
let PWD = fs.makeAbsolute(PWDRE.exec(stack)[1]);

let database = "_system";

const optionsDefaults = {
  disabledDbserverUUID: "",
  minReplicationFactor: 1,
  maxReplicationFactor: 2,
  readonly: false,
  numberOfDBs: 1,
  countOffset: 0,
  collectionMultiplier: 1,
  singleShard: false,
  progress: false,
  oldVersion: "3.5.0",
  testFoxx: true
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
  let now = time();
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


let v = db._version(true);
const enterprise = v.license === "enterprise";
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

  progress();
  let loopCount = 0;
  while (loopCount < options.collectionMultiplier) {

    // Check collections:
    progress();
    print(db._collections());
    CheckDataFuncs.forEach(func => {
      func(options,
           isCluster,
           enterprise,
           dbCount,
           loopCount);
    });
    loopCount++;
  }
  print(timeLine.join());
  dbCount++;
}
