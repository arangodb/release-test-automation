
// Use like this:
//   arangosh USUAL_OPTIONS_INCLUDING_AUTHENTICATION --javascript.execute checkdata.js [DATABASENAME]
// where DATABASENAME is optional and defaults to "_system".

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

    // Check collections:
    progress();

    let c = db._collection(`c_${ccount}`);
    let chash = db._collection(`chash_${ccount}`);
    let cskip = db._collection(`cskip_${ccount}`);
    let cfull = db._collection(`cfull_${ccount}`);
    let cgeo = db._collection(`cgeo_${ccount}`);
    let cunique = db._collection(`cunique_${ccount}`);
    let cmulti = db._collection(`cmulti_${ccount}`);
    let cempty = db._collection(`cempty_${ccount}`);

    // Check indexes:
    progress();

    if (c.getIndexes().length != 1) { throw "Banana"; }
    if (chash.getIndexes().length != 2) { throw "Apple"; }
    if (chash.getIndexes()[1].type != "hash") { throw "Pear"; }
    if (cskip.getIndexes().length != 2) { throw "Tomato"; }
    if (cskip.getIndexes()[1].type != "skiplist") { throw "Avocado"; }
    if (cfull.getIndexes().length != 2) { throw "Mango"; }
    if (cfull.getIndexes()[1].type != "fulltext") { throw "Cucumber"; }
    if (cgeo.getIndexes().length != 2) { throw "Jackfruit"; }
    if (cgeo.getIndexes()[1].type != "geo") { throw "Onion"; }
    if (cunique.getIndexes().length != 2) { throw "Durian"; }
    if (cunique.getIndexes()[1].unique != true) { throw "Mandarin"; }
    if (cmulti.getIndexes().length != 5) { throw "Leek"; }
    if (cempty.getIndexes().length != 1) { throw "Pineapple"; }

    // Check data:
    progress();
    if (c.count() != 1000) { throw "Audi"; }
    if (chash.count() != 12345) { throw "VW"; }
    if (cskip.count() != 2176) { throw "Tesla"; }
    if (cgeo.count() != 5245) { throw "Mercedes"; }
    if (cfull.count() != 6253) { throw "Renault"; }
    if (cunique.count() != 5362) { throw "Opel"; }
    if (cmulti.count() != 12346) { throw "Fiat"; }

    // Check a few queries:
    progress();
    if (db._query(`FOR x IN ${c.name()} FILTER x.a == "id1001" RETURN x`).toArray().length !== 1) { throw "Red Currant"; }
    progress();
    if (db._query(`FOR x IN ${chash.name()} FILTER x.a == "id10452" RETURN x`).toArray().length !== 1) { throw "Blueberry"; }
    progress();
    if (db._query(`FOR x IN ${cskip.name()} FILTER x.a == "id13948" RETURN x`).toArray().length !== 1) { throw "Grape"; }
    progress();
    if (db._query(`FOR x IN ${cempty.name()} RETURN x`).toArray().length !== 0) { throw "Grapefruit"; }
    progress();
    if (db._query(`FOR x IN ${cgeo.name()} FILTER x.a == "id20473" RETURN x`).toArray().length !== 1) { throw "Bean"; }
    progress();
    if (db._query(`FOR x IN ${cunique.name()} FILTER x.a == "id32236" RETURN x`).toArray().length !== 1) { throw "Watermelon"; }
    progress();
    if (db._query(`FOR x IN ${cmulti.name()} FILTER x.a == "id32847" RETURN x`).toArray().length !== 1) { throw "Honeymelon"; }
    progress();

    // Check view:
    let view1 = db._view(`view1_${ccount}`);
    if (! view1.properties().links.hasOwnProperty(`cview1_${ccount}`)) {throw "Hass"; }
    progress();

    // Check graph:

    let patents_naive = db._collection(`patents_naive_${ccount}`)
    if (patents_naive.count() !== 761) { throw "Orange"; }
    progress();
    let citations_naive = db._collection(`citations_naive_${ccount}`)
    if (citations_naive.count() !== 1000) { throw "Papaya"; }
    progress();
    if (db._query(`FOR v, e, p IN 1..10 OUTBOUND "${patents_naive.name()}/US:3858245" 
                 GRAPH "G_naive_${ccount}"
                 RETURN v`).toArray().length !== 6) { throw "Physalis"; }
    progress();
    if (enterprise){
      let patents_smart = db._collection(`patents_smart_${ccount}`)
      if (patents_smart.count() !== 761) { throw "Cherry"; }
      progress();
      let citations_smart = db._collection(`citations_smart_${ccount}`)
      if (citations_smart.count() !== 1000) { throw "Liji"; }
      progress();
      if (db._query(`FOR v, e, p IN 1..10 OUTBOUND "${patents_smart.name()}/US:3858245" 
                   GRAPH "G_smart_${ccount}"
                   RETURN v`).toArray().length !== 6) { throw "Black Currant"; }
      progress();
    }
    ccount ++;
  }
  print(timeLine.join());
  count ++;
}
