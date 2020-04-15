
// Use like this:
//   arangosh USUAL_OPTIONS_INCLUDING_AUTHENTICATION --javascript.execute makedata.js [DATABASENAME]
// where DATABASENAME is optional and defaults to "_system". The database
// in question is created (if it is not "_system").

let fs = require("fs");
let database = "_system";

let PWDRE = /.*at (.*)makedata.js.*/
let stack = new Error().stack;
let PWD=fs.makeAbsolute(PWDRE.exec(stack)[1]);
if (0 < ARGUMENTS.length) {
  database = ARGUMENTS[0];
}

if (database != "_system") {
  db._createDatabase(database);
  db._useDatabase(database);
}

// Create a few collections:

let c = db._create("c", {numberOfShards: 3, replicationFactor: 2});
let chash = db._create("chash", {numberOfShards: 3, replicationFactor: 2});
let cskip = db._create("cskip", {numberOfShards: 1, replicationFactor: 1});
let cfull = db._create("cfull", {numberOfShards: 3, replicationFactor: 1});
let cgeo = db._create("cgeo", {numberOfShards: 3, replicationFactor: 2});
let cunique = db._create("cunique", {numberOfShards: 1, replicationFactor: 1});
let cmulti = db._create("cmulti", {numberOfShards: 3, replicationFactor: 2});
let cempty = db._create("cempty", {numberOfShards: 3, replicationFactor: 1});

// Create some indexes:

chash.ensureIndex({type: "hash", fields: ["a"], unique: false});
cskip.ensureIndex({type: "skiplist", fields: ["a"], unique: false});
cfull.ensureIndex({type: "fulltext", fields: ["text"], minLength: 4});
cgeo.ensureIndex({type: "geo", fields: ["position"], geoJson: true});
cunique.ensureIndex({type: "hash", fields: ["a"], unique: true});
cmulti.ensureIndex({type: "hash", fields: ["a"], unique: false});
cmulti.ensureIndex({type: "skiplist", fields: ["b", "c"]});
cmulti.ensureIndex({type: "geo", fields: ["position"], geoJson: true});
cmulti.ensureIndex({type: "fulltext", fields: ["text"], minLength: 6});

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
}

let makeRandomNumber = function(low, high) {
  return (Math.abs(rand()) % (high - low)) + low;
}

let makeRandomTimeStamp = function() {
  return new Date(rand() * 1000).toISOString();
}

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
}

let writeData = function(coll, n) {
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
}

// Now the actual data writing:

writeData(c, 1000);
writeData(chash, 12345);
writeData(cskip, 2176);
writeData(cgeo, 5245);
writeData(cfull, 6253);
writeData(cunique, 5362);
writeData(cmulti, 12346);

let cview1 = db._create("cview1")
let view1 =  db._createView("view1", "arangosearch", {});
let meta = {links: {}};
meta.links["cview1"] = { includeAllFields: true}
view1.properties(meta)

cview1.insert({"animal": "cat", "name": "tom"}
             ,{"animal": "mouse", "name": "jerry"}
             ,{"animal": "dog", "name": "harry"}
             )

// Now create a graph:

let writeGraphData = function(V, E, vertnames, edgenames) {
  let vfile = fs.readFileSync(vertnames);
  let efile = fs.readFileSync(edgenames);
  let v = JSON.parse(vfile);
  let e = JSON.parse(efile);
  V.insert(v);
  E.insert(e);
}

let g = require("@arangodb/general-graph");
let G = g._create("G_naive",[g._relation("citations_naive",
                               ["patents_naive"],["patents_naive"])],
              [], {numberOfShards:3});
writeGraphData(db._collection("patents_naive"),
               db._collection("citations_naive"),
               `${PWD}/vertices.json`, `${PWD}/edges_naive.json`);


// And now a smart graph (if enterprise):

let v = db._connection.GET("/_api/version");
if (v.license !== "enterprise") {
  print("Not an enterprise version, not creating smart graph.");
} else {
  let gsm = require("@arangodb/smart-graph");
  let Gsm = gsm._create("G_smart",[gsm._relation("citations_smart",
                                     ["patents_smart"],["patents_smart"])],
                    [], {numberOfShards:3, smartGraphAttribute:"COUNTRY"});
  writeGraphData(db._collection("patents_smart"),
                 db._collection("citations_smart"),
               `${PWD}/vertices.json`, `${PWD}/edges.json`);
}
