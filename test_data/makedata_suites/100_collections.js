/* global print,  db, progress, createCollectionSafe, createIndexSafe, time  */
let rand = require("internal").rand;

(function () {
  return {
    isSupported: function (version, oldVersion, options, enterprise, cluster) {
      return true;
    },
    makeData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
      // All items created must contain dbCount and loopCount
      // Create a few collections:
      let c = createCollectionSafe(`c_${loopCount}`, 3, 2);
      progress('createCollection1');
      let chash = createCollectionSafe(`chash_${loopCount}`, 3, 2);
      progress('createCollection2');
      let cskip = createCollectionSafe(`cskip_${loopCount}`, 1, 1);
      progress('createCollection3');
      let cfull = createCollectionSafe(`cfull_${loopCount}`, 3, 1);
      progress('createCollection4');
      let cgeo = createCollectionSafe(`cgeo_${loopCount}`, 3, 2);
      progress('createCollectionGeo5');
      let cunique = createCollectionSafe(`cunique_${loopCount}`, 1, 1);
      progress('createCollection6');
      let cmulti = createCollectionSafe(`cmulti_${loopCount}`, 3, 2);
      progress('createCollection7');
      let cempty = createCollectionSafe(`cempty_${loopCount}`, 3, 1);

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

      let makeRandomString = function (l) {
        var r = rand();
        var d = rand();
        var s = "x";
        while (s.length < l) {
          s += r;
          r += d;
        }
        return s.slice(0, l);
      };

      let makeRandomNumber = function (low, high) {
        return (Math.abs(rand()) % (high - low)) + low;
      };

      let makeRandomTimeStamp = function () {
        return new Date(rand() * 1000).toISOString();
      };

      let rcount = 1; // for uniqueness

      let makeRandomDoc = function () {
        rcount += 1;
        let s = "";
        for (let i = 0; i < 10; ++i) {
          s += " " + makeRandomString(10);
        }
        return { Type: makeRandomNumber(1000, 65535),
                 ID: makeRandomString(40),
                 OptOut: rand() > 0 ? 1 : 0,
                 Source: makeRandomString(14),
                 dateLast: makeRandomTimeStamp(),
                 a: "id" + rcount,
                 b: makeRandomString(20),
                 c: makeRandomString(40),
                 text: s,
                 position: {type: "Point",
                            coordinates: [makeRandomNumber(0, 3600) / 10.0,
                                          makeRandomNumber(-899, 899) / 10.0]
                           }};
      };

      let writeData = function (coll, n) {
        let wcount = 0;
        while (wcount < options.dataMultiplier) {
          let l = [];
          let times = [];

          for (let i = 0; i < n; ++i) {
            l.push(makeRandomDoc());
            if (l.length % 1000 === 0 || i === n - 1) {
              let t = time();
              coll.insert(l);
              let t2 = time();
              l = [];
              // print(i+1, t2-t);
              times.push(t2 - t);
            }
          }
          // Timings, if ever needed:
          // times = times.sort(function(a, b) { return a-b; });
          // print(" Median:", times[Math.floor(times.length / 2)], "\n",
          //       "90%ile:", times[Math.floor(times.length * 0.90)], "\n",
          //       "99%ile:", times[Math.floor(times.length * 0.99)], "\n",
          //       "min   :", times[0], "\n",
          //       "max   :", times[times.length-1]);
          wcount += 1;
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
    },
    checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
      let cols = db._collections();
      let allFound = true;
      [`c_${loopCount}`,
       `chash_${loopCount}`,
       `cskip_${loopCount}`,
       `cfull_${loopCount}`,
       `cgeo_${loopCount}`,
       `cunique_${loopCount}`,
       `cmulti_${loopCount}`,
       `cempty_${loopCount}`].forEach(colname => {
         let foundOne = false;
         cols.forEach(oneCol => {
           if (oneCol.name() === colname) {
             foundOne = true;
           }
         });
         if (!foundOne) {
           print("Didn't find this collection: " + colname);
           allFound = false;
         }
       });
      if (!allFound) {
        throw new Error("not all collections were present on the system!");
      }

      let c = db._collection(`c_${loopCount}`);
      let chash = db._collection(`chash_${loopCount}`);
      let cskip = db._collection(`cskip_${loopCount}`);
      let cfull = db._collection(`cfull_${loopCount}`);
      let cgeo = db._collection(`cgeo_${loopCount}`);
      let cunique = db._collection(`cunique_${loopCount}`);
      let cmulti = db._collection(`cmulti_${loopCount}`);
      let cempty = db._collection(`cempty_${loopCount}`);

      // Check indexes:
      progress();

      if (c.getIndexes().length !== 1) { throw new Error(`Banana ${c.getIndexes().length}`); }
      if (chash.getIndexes().length !== 2) { throw new Error(`Apple ${chash.getIndexes().length}`); }
      if (chash.getIndexes()[1].type !== 'hash') { throw new Error(`Pear ${chash.getIndexes()[1].type}`); }
      if (cskip.getIndexes().length !== 2) { throw new Error(`Tomato ${cskip.getIndexes().length}`); }
      if (cskip.getIndexes()[1].type !== 'skiplist') { throw new Error(`Avocado ${cskip.getIndexes()[1].type}`); }
      if (cfull.getIndexes().length !== 2) { throw new Error(`Mango ${cfull.getIndexes().length}`); }
      if (cfull.getIndexes()[1].type !== 'fulltext') { throw new Error(`Cucumber ${cfull.getIndexes()[1].type}`); }
      if (cgeo.getIndexes().length !== 2) { throw new Error(`Jackfruit ${cgeo.getIndexes().length}`); }
      if (cgeo.getIndexes()[1].type !== 'geo') { throw new Error(`Onion ${cgeo.getIndexes()[1].type}`); }
      if (cunique.getIndexes().length !== 2) { throw new Error(`Durian ${cunique.getIndexes().length}`); }
      if (cunique.getIndexes()[1].unique !== true) { throw new Error(`Mandarin ${cunique.getIndexes()[1].unique}`); }
      if (cmulti.getIndexes().length !== 5) { throw new Error(`Leek ${cmulti.getIndexes().length}`); }
      if (cempty.getIndexes().length !== 1) { throw new Error(`Pineapple ${cempty.getIndexes().length}`); }

      // Check data:
      progress();
      if (c.count() !== 1000) { throw new Error(`Audi ${c.count()} !== 1000`); }
      if (chash.count() !== 12345) { throw new Error(`VW ${chash.count()} !== 12345`); }
      if (cskip.count() !== 2176) { throw new Error(`Tesla ${cskip.count()} !== 2176`); }
      if (cgeo.count() !== 5245) { throw new Error(`Mercedes ${cgeo.count()} !== 5245`); }
      if (cfull.count() !== 6253) { throw new Error(`Renault ${cfull.count()} !== 6253`); }
      if (cunique.count() !== 5362) { throw new Error(`Opel ${cunique.count()} !== 5362`); }
      if (cmulti.count() !== 12346) { throw new Error(`Fiat ${cmulti.count()} !== 12346`); }

      // Check a few queries:
      progress();
      if (db._query(`FOR x IN ${c.name()} FILTER x.a == "id1001" RETURN x`).toArray().length !== 1) { throw new Error("Red Currant"); }
      progress();
      if (db._query(`FOR x IN ${chash.name()} FILTER x.a == "id10452" RETURN x`).toArray().length !== 1) { throw new Error("Blueberry"); }
      progress();
      if (db._query(`FOR x IN ${cskip.name()} FILTER x.a == "id13948" RETURN x`).toArray().length !== 1) { throw new Error("Grape"); }
      progress();
      if (db._query(`FOR x IN ${cempty.name()} RETURN x`).toArray().length !== 0) { throw new Error("Grapefruit"); }
      progress();
      if (db._query(`FOR x IN ${cgeo.name()} FILTER x.a == "id20473" RETURN x`).toArray().length !== 1) { throw new Error("Bean"); }
      progress();
      if (db._query(`FOR x IN ${cunique.name()} FILTER x.a == "id32236" RETURN x`).toArray().length !== 1) { throw new Error("Watermelon"); }
      progress();
      if (db._query(`FOR x IN ${cmulti.name()} FILTER x.a == "id32847" RETURN x`).toArray().length !== 1) { throw new Error("Honeymelon"); }
      progress();
    },
    clearData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbCount} ${loopCount}`);
      try {
        db._drop(`c_${loopCount}`);
      } catch (e) {}
      progress();
      try {
        db._drop(`chash_${loopCount}`);
      } catch (e) {}
      progress();
      try {
        db._drop(`cskip_${loopCount}`);
      } catch (e) {}
      progress();
      try {
        db._drop(`cfull_${loopCount}`);
      } catch (e) {}
      progress();
      try {
        db._drop(`cgeo_${loopCount}`);
      } catch (e) {}
      progress();
      try {
        db._drop(`cunique_${loopCount}`);
      } catch (e) {}
      progress();
      try {
        db._drop(`cmulti_${loopCount}`);
      } catch (e) {}
      progress();
      try {
        db._drop(`cempty_${loopCount}`);
      } catch (e) {}
      progress();
    }
  };
}());
