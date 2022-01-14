
// Use like this:
//   arangosh USUAL_OPTIONS_INCLUDING_AUTHENTICATION --javascript.execute cleardata.js [DATABASENAME]
// where DATABASENAME is optional and defaults to "_system". The database
// in question is dropped (if it is not "_system").

const _ = require('lodash');
const internal = require('internal')
const arangodb = require("@arangodb");
const time = internal.time;
let db = internal.db;
let print = internal.print;
let database = "_system";
const ERRORS = arangodb.errors;

const optionsDefaults = {
  minReplicationFactor: 1,
  maxReplicationFactor: 2,
  numberOfDBs: 1,
  countOffset: 0,
  collectionMultiplier: 1,
  singleShard: false,
  progress: false
}

if ((0 < ARGUMENTS.length) &&
    (ARGUMENTS[0].slice(0, 1) !== '-')) {
  database = ARGUMENTS[0];
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
let ClearDataFuncs = [];
let ClearDataDbFuncs = [];
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
      if ('clearData' in suite) {
        ClearDataFuncs.push(suite.clearData);
      }
      if ('clearDataDB' in suite) {
        ClearDataDbFuncs.push(suite.clearDataDB);
      }
    }
  });
}

let v = db._connection.GET("/_api/version");
const enterprise = v.license === "enterprise"
scanTestPaths(options);
let count = 0;
while (count < options.numberOfDBs) {
  let databaseName = database
  tStart = time();
  timeLine = [tStart];
  ClearDataDbFuncs.forEach(func => {
    db._useDatabase("_system");
    func(options, isCluster, enterprise, database, count);
  });

  progress();
  ccount = 0;
  while (ccount < options.collectionMultiplier) {
    // Drop collections:
    ClearDataFuncs.forEach(func => {
      func(options, isCluster, enterprise,
           count,
           ccount);
    });

    progress();
    ccount ++;
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
  count ++;
}

