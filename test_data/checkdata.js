
// Use like this:
//   arangosh USUAL_OPTIONS_INCLUDING_AUTHENTICATION --javascript.execute checkdata.js [DATABASENAME]
// where DATABASENAME is optional and defaults to "_system".

let internal = require("internal");
let db = internal.db;
let print = internal.print;
let database = "_system";

if (0 < ARGUMENTS.length) {
  database = ARGUMENTS[0];
}

if (database != "_system") {
  db._useDatabase(database);
}

// Check collections:

let c = db._collection("c");
let chash = db._collection("chash");
let cskip = db._collection("cskip");
let cfull = db._collection("cfull");
let cgeo = db._collection("cgeo");
let cunique = db._collection("cunique");
let cmulti = db._collection("cmulti");
let cempty = db._collection("cempty");

// Check indexes:

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

if (c.count() != 1000) { throw "Audi"; }
if (chash.count() != 12345) { throw "VW"; }
if (cskip.count() != 2176) { throw "Tesla"; }
if (cgeo.count() != 5245) { throw "Mercedes"; }
if (cfull.count() != 6253) { throw "Renault"; }
if (cunique.count() != 5362) { throw "Opel"; }
if (cmulti.count() != 12346) { throw "Fiat"; }

// Check a few queries:
if (db._query(`FOR x IN c FILTER x.a == "id1001" RETURN x`).toArray().length !== 1) { throw "Red Currant"; }
if (db._query(`FOR x IN chash FILTER x.a == "id10452" RETURN x`).toArray().length !== 1) { throw "Blueberry"; }
if (db._query(`FOR x IN cskip FILTER x.a == "id13948" RETURN x`).toArray().length !== 1) { throw "Grape"; }
if (db._query(`FOR x IN cempty RETURN x`).toArray().length !== 0) { throw "Grapefruit"; }
if (db._query(`FOR x IN cgeo FILTER x.a == "id20473" RETURN x`).toArray().length !== 1) { throw "Bean"; }
if (db._query(`FOR x IN cunique FILTER x.a == "id32236" RETURN x`).toArray().length !== 1) { throw "Watermelon"; }
if (db._query(`FOR x IN cmulti FILTER x.a == "id32847" RETURN x`).toArray().length !== 1) { throw "Honeymelon"; }

// Check view:
let view1 = db._view("view1");
if (view1.properties().links.cview1 === undefined) {throw "Hass"; }

// Check graph:

if (db.patents_naive.count() !== 761) { throw "Orange"; }
if (db.citations_naive.count() !== 1000) { throw "Papaya"; }
if (db._query(`FOR v, e, p IN 1..10 OUTBOUND "patents_naive/US:3858245" 
                 GRAPH "G_naive"
                 RETURN v`).toArray().length !== 6) { throw "Physalis"; }
let v = db._connection.GET("/_api/version");
if (v.license !== "enterprise") {
  print("Not an enterprise version, not checking smart graph.");
} else {
  if (db.patents_smart.count() !== 761) { throw "Cherry"; }
  if (db.citations_smart.count() !== 1000) { throw "Liji"; }
  if (db._query(`FOR v, e, p IN 1..10 OUTBOUND "patents_smart/US:3858245" 
                   GRAPH "G_smart"
                   RETURN v`).toArray().length !== 6) { throw "Black Currant"; }
}
