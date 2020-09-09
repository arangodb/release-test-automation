
// Use like this:
//   arangosh USUAL_OPTIONS_INCLUDING_AUTHENTICATION --javascript.execute cleardata.js [DATABASENAME]
// where DATABASENAME is optional and defaults to "_system". The database
// in question is dropped (if it is not "_system").

const _ = require('lodash');
const internal = require('internal')
const time = internal.time;
let db = internal.db;
let print = internal.print;
let database = "_system";

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

let v = db._connection.GET("/_api/version");
const enterprise = v.license === "enterprise"

let count = 0;
while (count < options.numberOfDBs) {
  let databaseName = database
  tStart = time();
  timeLine = [tStart];
  db._useDatabase("_system");

  if (database != "_system") {
    print('#ix')
    c = zeroPad(count+options.countOffset);
    databaseName = `${database}_${c}`;
    db._useDatabase(databaseName);
  }
  else if (options.numberOfDBs > 1) {
    throw ("must specify a database prefix if want to work with multiple DBs.")
  }
  progress();
  ccount = 0;
  while (ccount < options.collectionMultiplier) {
    // Drop collections:

    try { db._drop(`c_${ccount}`); } catch (e) {}
    progress();
    try { db._drop(`chash_${ccount}`); } catch (e) {}
    progress();
    try { db._drop(`cskip_${ccount}`); } catch (e) {}
    progress();
    try { db._drop(`cfull_${ccount}`); } catch (e) {}
    progress();
    try { db._drop(`cgeo_${ccount}`); } catch (e) {}
    progress();
    try { db._drop(`cunique_${ccount}`); } catch (e) {}
    progress();
    try { db._drop(`cmulti_${ccount}`); } catch (e) {}
    progress();
    try { db._drop(`cempty_${ccount}`); } catch (e) {}
    progress();

    try { db._dropView(`view1_${ccount}`); } catch (e) { print(e); }
    progress();
    try { db._drop(`cview1_${ccount}`); } catch (e) { print(e); }
    progress();

    // Drop graph:

    let g = require("@arangodb/general-graph");
    progress();
    try { g._drop(`G_naive_${ccount}`, true); } catch(e) { }
    progress();
    if (enterprise) {
      let gsm = require("@arangodb/smart-graph");
      progress();
      try { gsm._drop(`G_smart_${ccount}`, true); } catch(e) { }
    }
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

