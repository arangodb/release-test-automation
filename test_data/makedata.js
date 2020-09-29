/* global print, start_pretty_print, ARGUMENTS */
//
// Use like this:
//   arangosh USUAL_OPTIONS_INCLUDING_AUTHENTICATION --javascript.execute makedata.js [DATABASENAME]
// where DATABASENAME is optional and defaults to "_system". The database
// in question is created (if it is not "_system").
// `--minReplicationFactor [1] don't create collections with smaller replication factor than this.
// `--maxReplicationFactor [2] don't create collections with a bigger replication factor than this.
// `--dataMultiplier [1]       0 - no data; else n-times the data
// `--numberOfDBs [1]          count of databases to create and fill
// `--countOffset [0]          number offset at which to start the database count
// `--collectionMultiplier [1] how many times to create the collections / index / view / graph set?
// `--singleShard [false]      whether this should only be a single shard instance
// `--progress [false]         whether to output a keepalive indicator to signal the invoker that work is ongoing

const _ = require('lodash');
const internal = require('internal');
const arangodb = require("@arangodb");
const console = require("console");
const fs = require("fs");
const db = internal.db;
const time = internal.time;
const sleep = internal.sleep;
const ERRORS = arangodb.errors;


let database = "_system";
let databaseName;

let PWDRE = /.*at (.*)makedata.js.*/;
let stack = new Error().stack;
let PWD=fs.makeAbsolute(PWDRE.exec(stack)[1]);
const optionsDefaults = {
  minReplicationFactor: 1,
  maxReplicationFactor: 2,
  numberOfDBs: 1,
  countOffset: 0,
  dataMultiplier: 1,
  collectionMultiplier: 1,
  singleShard: false,
  progress: false
};

let args = ARGUMENTS;
if ((0 < args.length) &&
    (args[0].slice(0, 1) !== '-')) {
  database = args[0];
  args = args.slice(1);
}

let options = internal.parseArgv(args, 0);
_.defaults(options, optionsDefaults);

var numberLength = Math.log(options.numberOfDBs + options.countOffset) * Math.LOG10E + 1 | 0;

const zeroPad = (num) => String(num).padStart(numberLength, '0');

let tStart = 0;
let timeLine = [];
function progress(gaugeName) {
  let now = time();
  let delta = now - tStart;
  timeLine.push(delta);
  if (options.progress) {
    print(`# - ${gaugeName},${tStart},${delta}`);
  }
  tStart = now;
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

function createSafe(name, fn1, fnErrorExists) {
  let countDbRetry = 0;
  while (countDbRetry < 50) {
    try {
      return fn1(name);
    } catch (x) {
      if (x.errorNum === ERRORS.ERROR_ARANGO_DUPLICATE_NAME.code) {
        console.error(`${databaseName}: ${name}: its already there? ${x.message} `);
        try {
          // make sure no local caches are there:
          arango.reconnect(arango.getEndpoint(), arango.getDatabaseName(), arango.connectedUser(), ''); // TODO passvoid?
          return fnErrorExists(name);
        }
        catch(x) {
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

function createCollectionSafe(name, DefaultNoSharts, DefaultReplFactor) {
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

function createIndexSafe(options) {
  opts = _.clone(options);
  delete opts.col
  return createSafe(options.col.name(), colname => {
    options.col.ensureIndex(opts);
  }, colName => {
    return false; // well, its there?
  });
}
let g = require("@arangodb/general-graph");
let v = db._connection.GET("/_api/version");
const enterprise = v.license === "enterprise";
let gsm;
if (enterprise) {
  gsm = require("@arangodb/smart-graph");
}

let vertices = JSON.parse(fs.readFileSync(`${PWD}/vertices.json`));
let edges = JSON.parse(fs.readFileSync(`${PWD}/edges_naive.json`));
let smart_edges = JSON.parse(fs.readFileSync(`${PWD}/edges.json`));
let count = 0;
while (count < options.numberOfDBs) {
  tStart = time();
  timeLine = [tStart];
  db._useDatabase("_system");
  if (database !== "_system") {
    print('#ix');
    let c = zeroPad(count+options.countOffset);
    databaseName = `${database}_${c}`;
    createSafe(databaseName,
               dbname => {
                 db._createDatabase(dbname);
                 return db._useDatabase(dbname);
               }, dbname => {
                 return db._useDatabase(databaseName);
               }
              );
  }
  else if (options.numberOfDBs > 1) {
    throw ("must specify a database prefix if want to work with multiple DBs.");
  }
  progress('createDB');

  let ccount = 0;
  while (ccount < options.collectionMultiplier) {
    // Create a few collections:
    let c = createCollectionSafe(`c_${ccount}`, 3, 2);
    progress('createCollection1');
    let chash = createCollectionSafe(`chash_${ccount}`, 3, 2);
    progress('createCollection2');
    let cskip = createCollectionSafe(`cskip_${ccount}`, 1, 1);
    progress('createCollection3');
    let cfull = createCollectionSafe(`cfull_${ccount}`, 3, 1);
    progress('createCollection4');
    let cgeo = createCollectionSafe(`cgeo_${ccount}`, 3, 2);
    progress('createCollectionGeo5');
    let cunique = createCollectionSafe(`cunique_${ccount}`, 1, 1);
    progress('createCollection6');
    let cmulti = createCollectionSafe(`cmulti_${ccount}`, 3, 2);
    progress('createCollection7');
    let cempty = createCollectionSafe(`cempty_${ccount}`, 3, 1);

    // Create some indexes:
    progress('createCollection8');
    createIndexSafe({col: chash, type: "hash", fields: ["a"], unique: false});
    progress('createIndexHash1');
    createIndexSafe({col: cskip, type: "skiplist", fields: ["a"], unique: false});
    progress('createIndexSkiplist2');
    createIndexSafe({col: cfull, type: "fulltext", fields: ["text"], minLength: 4});
    progress('createIndexFulltext3');
    createIndexSafe({col: cgeo, type: "geo", fields: ["position"], geoJson: true});
    progress('createIndexGeo4');
    createIndexSafe({col: cunique, type: "hash", fields: ["a"], unique: true});
    progress('createIndex5');
    createIndexSafe({col: cmulti, type: "hash", fields: ["a"], unique: false});
    progress('createIndex6');
    createIndexSafe({col: cmulti, type: "skiplist", fields: ["b", "c"]});
    progress('createIndex7');
    createIndexSafe({col: cmulti, type: "geo", fields: ["position"], geoJson: true});
    progress('createIndexGeo8');
    createIndexSafe({col: cmulti, type: "fulltext", fields: ["text"], minLength: 6});
    progress('createIndexFulltext9');

    // Put some data in:

    // Some helper functions:

    let rand = require("internal").rand;
    let time = require("internal").time;

    let makeRandomString = function(l) {
      var r = rand();
      var d = rand();
      var s = "x";
      while (s.length < l) {
        s += r;
        r += d;
      }
      return s.slice(0, l);
    };

    let makeRandomNumber = function(low, high) {
      return (Math.abs(rand()) % (high - low)) + low;
    };

    let makeRandomTimeStamp = function() {
      return new Date(rand() * 1000).toISOString();
    };

    let count = 1;   // for uniqueness

    let makeRandomDoc = function() {
      count += 1;
      let s = "";
      for (let i = 0; i < 10; ++i) {
        s += " " + makeRandomString(10);
      }
      return { Type: makeRandomNumber(1000, 65535),
               ID: makeRandomString(40),
               OptOut: rand() > 0 ? 1 : 0,
               Source: makeRandomString(14),
               dateLast: makeRandomTimeStamp(),
               a: "id" + count,
               b: makeRandomString(20),
               c: makeRandomString(40),
               text: s,
               position: {type: "Point",
                          coordinates: [makeRandomNumber(0, 3600) / 10.0,
                                        makeRandomNumber(-899, 899) / 10.0]
                         }};
    };

    let writeData = function(coll, n) {
      let count = 0;
      while (count < options.dataMultiplier) {
        let l = [];
        let times = [];

        for (let i = 0; i < n; ++i) {
          l.push(makeRandomDoc());
          if (l.length % 1000 === 0 || i === n-1) {
            let t = time();
            coll.insert(l);
            let t2 = time();
            l = [];
            //print(i+1, t2-t);
            times.push(t2-t);
          }
        }
        // Timings, if ever needed:
        //times = times.sort(function(a, b) { return a-b; });
        //print(" Median:", times[Math.floor(times.length / 2)], "\n",
        //      "90%ile:", times[Math.floor(times.length * 0.90)], "\n",
        //      "99%ile:", times[Math.floor(times.length * 0.99)], "\n",
        //      "min   :", times[0], "\n",
        //      "max   :", times[times.length-1]);
        count += 1;
      }
    };

    // Now the actual data writing:

    writeData(c, 1000);
    progress('writeData1');
    writeData(chash, 12345);
    progress('writeData2');
    writeData(cskip, 2176);
    progress('writeData3');
    writeData(cgeo, 5245);
    progress('writeData4');
    writeData(cfull, 6253);
    progress('writeData5');
    writeData(cunique, 5362);
    progress('writeData6');
    writeData(cmulti, 12346);
    progress('writeData7');

    let viewCollectionName = `cview1_${ccount}`;
    let cview1 = createSafe(viewCollectionName,
                            viewCollection => {
                              return db._create(viewCollection);
                            }, viewCollection => {
                              return db._collection(viewCollection);
                            }
                           );
    progress('createView1');
    let viewName1 = `view1_${ccount}`;
    let view1 = createSafe(viewName1,
                           viewname => {
                             return db._createView(viewname, "arangosearch", {});
                           }, viewname => {
                             return db._view(viewname);
                           }
                          );
    progress('createView2');
    let meta = {links: {}};
    meta.links[viewCollectionName] = { includeAllFields: true};
    view1.properties(meta);

    cview1.insert({"animal": "cat", "name": "tom"}
                  ,{"animal": "mouse", "name": "jerry"}
                  ,{"animal": "dog", "name": "harry"}
                 );
    progress('createView3');

    // Now create a graph:

    let writeGraphData = function(V, E, vertices, edges) {
      let count = 0;
      while (count < options.dataMultiplier) {
        edges.forEach(edg => {
          edg._from = V.name() + count + '/' + edg._from.split('/')[1];
          edg._to = V.name() + count + '/' + edg._to.split('/')[1];
        });

        let cVertices = _.clone(vertices);
        cVertices.forEach(vertex => {
          vertex['_key'] = vertex['_key'] + count;
        });

        V.insert(vertices);
        E.insert(edges);
        count += 1;
      }
    };

    let G = g._create(`G_naive_${ccount}`,[
      g._relation(`citations_naive_${ccount}`,
                  [`patents_naive_${ccount}`],
                  [`patents_naive_${ccount}`])],
                      [], {
                        numberOfShards:getShardCount(3)});
    progress('createGraph1');
    writeGraphData(db._collection(`patents_naive_${ccount}`),
                   db._collection(`citations_naive_${ccount}`),
                   _.clone(vertices), _.clone(edges));
    progress('loadGraph1');

    // And now a smart graph (if enterprise):
    if (enterprise) {
      let Gsm = gsm._create(`G_smart_${ccount}`, [
        gsm._relation(`citations_smart_${ccount}`,
                      [`patents_smart_${ccount}`],
                      [`patents_smart_${ccount}`])],
                            [], {numberOfShards: getShardCount(3), smartGraphAttribute:"COUNTRY"});
      progress('createEGraph2');
      writeGraphData(db._collection(`patents_smart_${ccount}`),
                     db._collection(`citations_smart_${ccount}`),
                     _.clone(vertices), _.clone(smart_edges));
      progress('writeEGraph2');
    }
    ccount ++;
  }
  console.error(timeLine.join());
  count ++;
}
