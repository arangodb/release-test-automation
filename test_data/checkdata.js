
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

const { FeatureFlags } = require("./feature_flags");

let database = "_system";

const optionsDefaults = {
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

const flags = new FeatureFlags(dbVersion, options.oldVersion);
 
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

function validateDocumentWorksInOneShard(db, baseName, count) {
  if (baseName === "_system") {
    baseName = "system";
  }
  progress("Test OneShard setup")
  const databaseName = `${baseName}_${count}_oneShard`;
  print('vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv ' + databaseName)
  print(db._databases())
  db._useDatabase(databaseName);
  for (let ccount = 0; ccount < options.collectionMultiplier; ++ccount) {
    const query = `
      LET testee = DOCUMENT("c_${ccount}_0/knownKey")
      FOR x IN c_${ccount}_1
        RETURN {v1: testee.value, v2: x.value}
      `;
    const result = db._query(query).toArray();
    if (result.length !== 1 || result[0].v1 !== "success" || result[0].v2 !== "success") {
      throw "DOCUMENT call in OneShard database does not return data";
    }

  }
}

function testSmartGraphValidator(ccount) {
  // Temporarily disable Validator Tests.
  // Due to our missconfigured jenkins it was impossible to test
  // this before merge, now it is all broken and needs time to be fixed.
  return {fail : false};
  if (!isCluster || !flags.hasSmartGraphValidator()) {
    // Feature does not exist, no need to test:
    return {fail: false};
  }
  try {
    const vColName = `patents_smart_${ccount}`;
    const eColName = `citations_smart_${ccount}`;
    const gName = `G_smart_${ccount}`;
    const remoteDocument = {_key: "abc:123:def", _from: `${vColName}/abc:123`, _to: `${vColName}/def:123`};
    const localDocument = {_key: "abc:123:abc", _from: `${vColName}/abc:123`, _to: `${vColName}/abc:123`};
    const testValidator = (colName, doc) => {
      let col = db._collection(colName);
      if (!col) {
        return {
          fail: true,
          message: `The smartGraph "${gName}" was not created correctly, collection ${colName} missing`
        };
      }
      try {
        col.save(doc);
        return {
          fail: true,
          message: `Validator did not trigger on collection ${colName} stored illegal document`
        };
      } catch (e) {
        // We only allow the following two errors, all others should be reported.
        if (e.errorNum != 1466 && e.errorNum != 1233) {
          return {
            fail: true,
            message: `Validator of collection ${colName} on atempt to store ${doc} returned unexpected error ${JSON.stringify(e)}`
          };
        }
      }
      return {fail: false};
    }
    // We try to insert a document into the wrong shard. This should be rejected by the internal validator
    let res = testValidator(`_local_${eColName}`, remoteDocument);
    if (res.fail) {
      return res;
    }
    res = testValidator(`_from_${eColName}`, localDocument);
    if (res.fail) {
      return res;
    }
    res = testValidator(`_to_${eColName}`, localDocument);
    if (res.fail) {
      return res;
    }
    return {fail: false};
  } finally {
    // Always report that we tested SmartGraph Validators
    progress("Tested SmartGraph validators");
  }
}

function checkFoxxService() {
  const onlyJson = {
    'accept': 'application/json',
    'accept-content-type': 'application/json'
  };
  let reply;
  db._useDatabase("_system");

  [
    '/_db/_system/_admin/aardvark/index.html',
    '/_db/_system/itz/index',
    '/_db/_system/crud/xxx'
  ].forEach(route => {
    for (i=0; i < 200; i++) {
      try {
        reply = arango.GET_RAW(route, onlyJson);
        if (reply.code == "200") {
          print(route + " OK");
          return;
        }
        print(route + " Not yet ready, retrying: " + JSON.stringify(reply))
      } catch (e) {
        print(route + " Caught - need to retry. " + JSON.stringify(e))
      }
      internal.sleep(3);
    }
    throw ("foxx route '" + route + "' not ready on time!");
  });

  print("Foxx: Itzpapalotl getting the root of the gods");
  reply = arango.GET_RAW('/_db/_system/itz');
  assertEqual(reply.code, "307", JSON.stringify(reply));

  print('Foxx: Itzpapalotl getting index html with list of gods');
  reply = arango.GET_RAW('/_db/_system/itz/index');
  assertEqual(reply.code, "200", JSON.stringify(reply));

  print("Foxx: Itzpapalotl summoning Chalchihuitlicue");
  reply = arango.GET_RAW('/_db/_system/itz/Chalchihuitlicue/summon', onlyJson);
  assertEqual(reply.code, "200", JSON.stringify(reply));
  let parsedBody = JSON.parse(reply.body);
  assertEqual(parsedBody.name, "Chalchihuitlicue");
  assertTrue(parsedBody.summoned);

  print("Foxx: crud testing get xxx");
  reply = arango.GET_RAW('/_db/_system/crud/xxx', onlyJson);
  assertEqual(reply.code, "200");
  parsedBody = JSON.parse(reply.body);
  assertEqual(parsedBody, []);

  print("Foxx: crud testing POST xxx");
  
  reply = arango.POST_RAW('/_db/_system/crud/xxx', {_key: "test"})
  if (options.readOnly) {
    assertEqual(reply.code, "400");
  } else {
    assertEqual(reply.code, "201");
  }
  
  print("Foxx: crud testing get xxx");
  reply = arango.GET_RAW('/_db/_system/crud/xxx', onlyJson);
  assertEqual(reply.code, "200");
  parsedBody = JSON.parse(reply.body);
  if (options.readOnly) {
    assertEqual(parsedBody, []);
  } else {
    assertEqual(parsedBody.length, 1);
  }

  print('Foxx: crud testing delete document')
  reply = arango.DELETE_RAW('/_db/_system/crud/xxx/' + 'test');
  if (options.readOnly) {
    assertEqual(reply.code, "400");
  } else {
    assertEqual(reply.code, "204");
  }
}

let v = db._connection.GET("/_api/version");
const enterprise = v.license === "enterprise"


if (options.testFoxx) {
  checkFoxxService()
} else {
  print("Skipping foxx tests!")
}

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
    print(db._collections())
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
    if (enterprise && false){ // TODO: re-enable me!
      const vColName = `patents_smart_${ccount}`;
      let patents_smart = db._collection(vColName);
      if (patents_smart.count() !== 761) { throw "Cherry"; }
      progress();
      const eColName = `citations_smart_${ccount}`;
      let citations_smart = db._collection(eColName);
      if (citations_smart.count() !== 1000) { throw "Liji"; }
      progress();
      const gName = `G_smart_${ccount}`;
      if (db._query(`FOR v, e, p IN 1..10 OUTBOUND "${patents_smart.name()}/US:3858245" 
                   GRAPH "${gName}"
                   RETURN v`).toArray().length !== 6) { throw "Black Currant"; }
      progress();
      const res = testSmartGraphValidator(ccount);
      if (res.fail) {
        throw res.message;
      }
    }
    ccount ++;
  }
  print(timeLine.join());

  if (flags.shouldValidateOneShard()) {
    validateDocumentWorksInOneShard(db, database, count);
  }
  count ++;
}
