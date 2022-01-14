
// Use like this:
//   arangosh USUAL_OPTIONS_INCLUDING_AUTHENTICATION --javascript.execute checkdata.js [DATABASENAME]
// where DATABASENAME is optional and defaults to "_system".

const _ = require('lodash');
const internal = require('internal')
const time = internal.time;
let db = internal.db;
let print = internal.print;
const isCluster = require("internal").isCluster();
const dbVersion = db._version();
const {
  assertTrue,
  assertFalse,
  assertEqual,
  assertNotEqual,
  assertException
} = require("jsunity").jsUnity.assertions;


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

if ((0 < ARGUMENTS.length) &&
    (ARGUMENTS[0].slice(0, 1) !== '-')) {
  database = ARGUMENTS[0]; // must start with 'system_' else replication fuzzing may delete it!
  ARGUMENTS=ARGUMENTS.slice(1);
}

let options = internal.parseArgv(ARGUMENTS, 0);
_.defaults(options, optionsDefaults);


var numberLength = Math.log(options.numberOfDBs + options.countOffset) * Math.LOG10E + 1 | 0;

const zeroPad = (num) => String(num).padStart(numberLength, '0')
let tStart = 0;
let timeLine = [];
function progress() {
  now = time();
  timeLine.push(now - tStart);
  tStart = now;
  if (options.progress) {
    print("#");
  }
}
 
function getShardCount(defaultShardCount) {
  if (options.singleShard) {
    return 1;
  }
  return defaultShardCount;
}
function getReplicationFactor(defaultReplicationFactor) {
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
function scanTestPaths ( options) {
  
  let suites = _.filter(fs.list(fs.join(PWD,'makedata_suites')),
                  function (p) {
                    return (p.substr(-3) === '.js');
                  })
      .map(function (x) {
        return fs.join(fs.join(PWD, 'makedata_suites'), x);
      }).sort();
  suites.forEach(suitePath => {
    let suite = require("internal").load(suitePath);
    if (suite.isSupported(dbVersion, options.oldVersion, options, enterprise, false)) {
      print("supported")
      if ('checkData' in suite) {
        CheckDataFuncs.push(suite.checkData);
      }
      if ('checkDataDB' in suite) {
        CheckDataDbFuncs.push(suite.checkDataDB);
      }
    }
  });
}


let v = db._connection.GET("/_api/version");
const enterprise = v.license === "enterprise"
scanTestPaths(options);
let count = 0;
while (count < options.numberOfDBs) {
  tStart = time();
  timeLine = [tStart];
  db._useDatabase("_system");

  CheckDataDbFuncs.forEach(func => {
    db._useDatabase("_system");
    func(options, isCluster, enterprise, database, count);
  });
  
  progress();
  ccount = 0;
  while (ccount < options.collectionMultiplier) {

    // Check collections:
    progress();
    print(db._collections())
    CheckDataFuncs.forEach(func => {
      func(options, isCluster, enterprise,
           count,
           ccount);
    });
    ccount ++;
  }
  print(timeLine.join());
  count ++;
}
