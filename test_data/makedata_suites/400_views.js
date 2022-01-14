
(function () {
  return {
    isSupported: function(version, oldVersion, enterprise, cluster) {
      return true;
    },

    makeDataDB: function(options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      print(`making per database data ${dbCount}`);
    },
    makeData: function(options, isCluster, isEnterprise, dbCount, loopCount) {
      // All items created must contain dbCount and loopCount
      print(`making data ${dbCount} ${loopCount}`);
      let viewCollectionName = `cview1_${loopCount}`;
      let cview1 = createCollectionSafe(viewCollectionName, 3, 1);
      progress('createView1');
      let viewName1 = `view1_${loopCount}`;
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

    },
    checkData: function(options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbConut} ${loopCount}`);
      // Check view:
      let view1 = db._view(`view1_${loopCount}`);
      if (! view1.properties().links.hasOwnProperty(`cview1_${loopCount}`)) {throw "Hass"; }
      progress();
    },
    clearData: function(options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
      print(`checking data ${dbConut} ${loopCount}`);

      try { db._dropView(`view1_${loopCount}`); } catch (e) { print(e); }
      progress();
      try { db._drop(`cview1_${loopCount}`); } catch (e) { print(e); }
      progress();

    }
  };

}())
