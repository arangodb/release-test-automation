/*jshint globalstrict:false, strict:false, maxlen: 500 */
/*global assertUndefined, assertEqual, assertNotEqual, assertTrue, assertFalse, fail*/

////////////////////////////////////////////////////////////////////////////////
/// DISCLAIMER
///
/// Copyright 2020 ArangoDB GmbH, Cologne, Germany
///
/// Licensed under the Apache License, Version 2.0 (the "License");
/// you may not use this file except in compliance with the License.
/// You may obtain a copy of the License at
///
///     http://www.apache.org/licenses/LICENSE-2.0
///
/// Unless required by applicable law or agreed to in writing, software
/// distributed under the License is distributed on an "AS IS" BASIS,
/// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
/// See the License for the specific language governing permissions and
/// limitations under the License.
///
/// Copyright holder is ArangoDB GmbH, Cologne, Germany
///
/// @author Andrey Abramov
////////////////////////////////////////////////////////////////////////////////

const jsunity = require("jsunity");
const _ = require('lodash');
const {
  assertEqual, assertNotEqual,
  assertTrue, assertFalse,
  assertNull, assertNotNull,
  assertIdentical, assertNotIdentical,
  assertMatch, assertNotMatch,
  assertTypeOf, assertNotTypeOf,
  assertInstanceOf, assertNotInstanceOf,
  assertUndefined, assertNotUndefined,
  assertNan, assertNotNan,
  fail } = jsunity.jsUnity.assertions;
const db = require("@arangodb").db;
const analyzers = require("@arangodb/analyzers");

const noOptimization = {optimizer: {rules:["-all"]}};
const noSubquerySplicing= {optimizer: {rules:["-splice-subqueries"]}};
const noLateMaterialization = {optimizer: {rules:["-late-document-materialization-arangosearch"]}};
const materialize = {noMaterialization:false};
const doNotMaterialize = {noMaterialization:true};

function getNodes(query, type, bindVars, options) {
  let stmt = db._createStatement(query);
  if (typeof bindVars === "object") {
    stmt.bind(bindVars)
  }
  if (typeof options === "object") {
    stmt.setOptions(options)
  }
  return stmt.explain()
             .plan
             .nodes
             .filter(node => node.type === type);
}

////////////////////////////////////////////////////////////////////////////////
/// @brief test suite
/// @note the suite expects the following database objects to be available
///         - document collection 'wikipedia'
///         - edge collection 'links'
///         - arangosearch view 'v_wiki_stored'
///           {
///             storedValues: [
///               ["created"],
///               ["title", "created", "count", "_id"],
///               ["invalidField"]
///             ],
///             links : { wikipedia : { includeAllFields: true, } }
///           }
///         - arangosearch view 'v_wiki_sorted'
///           {
///             primarySort: [
///               { field: "_key", asc:true },
///               { field: "body", asc:true },
///               { field: "created", asc:true },
///               { field: "title", asc:true },
///               { field: "count", asc:true },
///               { field: "_id", asc:true },
///               { field: "_rev", asc:true },
///             ],
///             links : { wikipedia : { includeAllFields: true } }
///           }
////////////////////////////////////////////////////////////////////////////////

function ArangoSearch_StoredValues() {
  return {
    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure document isn't materialized
    /// 2. ensure subquery splicing is disabled
    /// 3. ensure arangosearch reads all values from ["title", "created", "count", "_id"]
    ///    and primarySort columns
    /// 4. ensure results are same as for collection with filter
    /// 5. ensure results are same as for view without stored values
    ////////////////////////////////////////////////////////////////////////////////
    testNoMaterializationForSubQueryWithoutSplicing: function () {
      let query = `
        FOR d IN v_wiki_stored
          SEARCH IN_RANGE(d.count, 99, 9999, true, true)
          OPTIONS { noMaterialization: @noMaterialization }
        SORT d._id
        RETURN { title: d.title, counts: (FOR j IN d.count..d.count+10 RETURN j) }`;

      assertEqual(0, getNodes(query, "SubqueryStartNode", doNotMaterialize, noSubquerySplicing).length);
      assertEqual(0, getNodes(query, "SubqueryStartNode", materialize, noSubquerySplicing).length);

      {
        let viewNodes = getNodes(query, "EnumerateViewNode", doNotMaterialize, noSubquerySplicing)
        assertEqual(1, viewNodes.length);

        let viewWithStoredValues = viewNodes.find(v => v.view === "v_wiki_stored");
        assertNotUndefined(viewWithStoredValues);
        assertTrue(viewWithStoredValues.noMaterialization);
        assertEqual(1, viewWithStoredValues.viewValuesVars.length);
        assertEqual(["_id", "count", "title"],
                    viewWithStoredValues.viewValuesVars[0].viewStoredValuesVars.map(v => v.field).sort());
      }

      {
        let viewNodes = getNodes(query, "EnumerateViewNode", materialize, noSubquerySplicing);
        assertEqual(1, viewNodes.length);
        assertFalse(viewNodes[0].noMaterialization);
        assertEqual(0, viewNodes[0].viewValuesVars.length);
      }

      let expected = db._query(`
        FOR d IN wikipedia FILTER IN_RANGE(d.count, 99, 9999, true, true)
        SORT d._id
        RETURN { title: d.title, counts: (FOR j IN d.count..d.count+10 RETURN j) }`, {}, noOptimization).toArray();
      assertNotEqual(expected.length, 0);

      let actual = db._query(query, doNotMaterialize, noSubquerySplicing).toArray();
      assertEqual(expected.length, actual.length);
      actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));

      let actualEarlyMaterialization = db._query(query, materialize, noSubquerySplicing).toArray();
      assertEqual(expected.length, actualEarlyMaterialization.length);
      actualEarlyMaterialization.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));
    },

    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure document isn't materialized
    /// 2. ensure arangosearch reads all values from ["title", "created", "count", "_id"]
    ///    and primarySort columns
    /// 3. ensure results are same as for collection with filter
    /// 4. ensure results are same as for view without stored values
    ////////////////////////////////////////////////////////////////////////////////
    testNoMaterializationForSubQuery: function () {
      let query = `
        FOR d IN v_wiki_stored
          SEARCH IN_RANGE(d.count, 99, 9999, true, true)
          OPTIONS { noMaterialization: @noMaterialization }
        SORT d._id
        RETURN { title: d.title, counts: (FOR j IN d.count..d.count+10 RETURN j) }`;

      {
        let viewNodes = getNodes(query, "EnumerateViewNode", doNotMaterialize)
        assertEqual(1, viewNodes.length);

        let viewWithStoredValues = viewNodes.find(v => v.view === "v_wiki_stored");
        assertNotUndefined(viewWithStoredValues);
        assertTrue(viewWithStoredValues.noMaterialization);
        assertEqual(1, viewWithStoredValues.viewValuesVars.length);
        assertEqual(["_id", "count", "title"],
                    viewWithStoredValues.viewValuesVars[0].viewStoredValuesVars.map(v => v.field).sort());
      }

      {
        let viewNodes = getNodes(query, "EnumerateViewNode", materialize);
        assertEqual(1, viewNodes.length);
        assertFalse(viewNodes[0].noMaterialization);
        assertEqual(0, viewNodes[0].viewValuesVars.length);
      }

      let expected = db._query(`
        FOR d IN wikipedia FILTER IN_RANGE(d.count, 99, 9999, true, true)
        SORT d._id
        RETURN { title: d.title, counts: (FOR j IN d.count..d.count+10 RETURN j) }`, {}, noOptimization).toArray();
      assertNotEqual(expected.length, 0);

      let actual = db._query(query, doNotMaterialize).toArray();
      assertEqual(expected.length, actual.length);
      actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));

      let actualEarlyMaterialization = db._query(query, materialize).toArray();
      assertEqual(expected.length, actualEarlyMaterialization.length);
      actualEarlyMaterialization.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));
    },


    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure view node doesn't materialize documents
    /// 2. ensure arangosearch reads all values from ['title'] column
    /// 3. ensure MATERIALIZE node is present
    /// 4. ensure results are same as for collection with filter
    /// 5. ensure results are same as for query with late materialization disabled
    ////////////////////////////////////////////////////////////////////////////////
    testLateMaterialization: function () {
      let query = `
        FOR d IN v_wiki_stored 
          SEARCH IN_RANGE(d.count, 99, 99999, true, true)
          SORT d.title, d._id
          LIMIT 2013
        RETURN d`;

      let viewNode = getNodes(query, "EnumerateViewNode")[0];
      assertNotUndefined(viewNode);
      assertUndefined(viewNode.noMaterialization);
      assertEqual(1, viewNode.viewValuesVars.length);
      let viewValues = viewNode.viewValuesVars[0];
      assertEqual(2, viewValues.viewStoredValuesVars.length);
      assertEqual("title", viewValues.viewStoredValuesVars[0].field);
      assertEqual("_id", viewValues.viewStoredValuesVars[1].field);
      let materializationNode = getNodes(query, "MaterializeNode");
      assertNotUndefined(materializationNode);

      let viewNodeNoLateMaterialization = getNodes(query, "EnumerateViewNode", {}, noOptimization)[0];
      assertNotUndefined(viewNodeNoLateMaterialization);
      assertUndefined(viewNodeNoLateMaterialization.noMaterialization);
      assertEqual(0, viewNodeNoLateMaterialization.viewValuesVars.length);
      assertUndefined(getNodes(query, "MaterializeNode", {}, noOptimization)[0]);

      let expected = db._query(`
        FOR d IN wikipedia 
          FILTER IN_RANGE(d.count, 99, 99999, true, true)
          SORT d.title, d._id
          LIMIT 2013
          RETURN d`, {}, noOptimization).toArray();
      assertNotEqual(expected.length, 0);

      let actual = db._query(query).toArray();
      assertEqual(expected.length, actual.length);
      actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));

      let actualEarlyMaterialization = db._query(query, {}, noLateMaterialization).toArray();
      assertEqual(expected.length, actualEarlyMaterialization.length);
      actualEarlyMaterialization.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));
    },

    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure document isn't materialized
    /// 2. ensure arangosearch reads all values from ['title'] column
    /// 3. ensure results are same as for collection with filter
    /// 4. ensure results are same as for view without stored values
    ////////////////////////////////////////////////////////////////////////////////
    testNoMaterializationForReturn: function () {
      let query = `
        FOR d IN v_wiki_stored 
          SEARCH IN_RANGE(d.count, 99, 99999, true, true)
          OPTIONS { noMaterialization: @noMaterialization }
        RETURN d.title`;

      let noMaterializationNode = getNodes(query, "EnumerateViewNode", doNotMaterialize)[0];
      assertNotUndefined(noMaterializationNode);
      assertTrue(noMaterializationNode.noMaterialization);
      assertEqual(1, noMaterializationNode.viewValuesVars.length);
      let viewValues = noMaterializationNode.viewValuesVars[0];
      assertEqual(1, viewValues.viewStoredValuesVars.length);
      assertEqual("title", viewValues.viewStoredValuesVars[0].field);

      let node = getNodes(query, "EnumerateViewNode", materialize)[0];
      assertNotUndefined(node);
      assertFalse(node.noMaterialization);
      assertEqual(0, node.viewValuesVars.length);

      let expected = db._query(`
        FOR d IN wikipedia FILTER IN_RANGE(d.count, 99, 99999, true, true)
        RETURN d.title`, {}, noOptimization).toArray().sort();
      assertNotEqual(expected.length, 0);

      let actual = db._query(query, doNotMaterialize).toArray().sort();
      assertEqual(expected, actual);
      assertEqual(db._query(query, materialize).toArray().sort(), actual);
    },

    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure document isn't materialized
    /// 2. ensure SORT node is present
    /// 3. ensure arangosearch reads all values from prmarySort column
    /// 4. ensure results are same as for collection with filter
    /// 5. ensure results are same as for view without stored values
    ////////////////////////////////////////////////////////////////////////////////
    testNoMaterializationPrimarySort: function () {
      let query = `
        FOR d IN v_wiki_sorted
          SEARCH IN_RANGE(d.count, 99, 99999, true, true)
          OPTIONS { noMaterialization: @noMaterialization }
          SORT d.title, d._key
        RETURN { body: d.body, title: d.title }`;

      assertEqual(1, getNodes(query, "SortNode", doNotMaterialize).length);
      assertEqual(1, getNodes(query, "SortNode", materialize).length);

      let noMaterializationNode = getNodes(query, "EnumerateViewNode", doNotMaterialize)[0];
      assertNotUndefined(noMaterializationNode);
      assertTrue(noMaterializationNode.noMaterialization);
      assertEqual(["_key", "body","title"],
                  noMaterializationNode.viewValuesVars.map(v => v.field).sort());

      let node = getNodes(query, "EnumerateViewNode", materialize)[0];
      assertNotUndefined(node);
      assertFalse(node.noMaterialization);
      assertEqual(0, node.viewValuesVars.length);

      let expected = db._query(`
        FOR d IN wikipedia FILTER IN_RANGE(d.count, 99, 99999, true, true)
        SORT d.title, d._key
        RETURN { title: d.title, body: d.body }`, {}, noOptimization).toArray();
      assertNotEqual(expected.length, 0);

      let actual = db._query(query, doNotMaterialize).toArray().sort();
      assertEqual(expected.length, actual.length);
      actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));

      let actualEarlyMaterialization = db._query(query, materialize).toArray().sort();
      assertEqual(expected.length, actualEarlyMaterialization.length);
      actualEarlyMaterialization.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));
    },

    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure document isn't materialized
    /// 2. ensure SORT node isn't present
    /// 3. ensure arangosearch reads all values from prmarySort column
    /// 4. ensure results are same as for collection with filter
    /// 5. ensure results are same as for view without stored values
    ////////////////////////////////////////////////////////////////////////////////
    testNoMaterializationOptimizedSortPrimarySort: function () {
      let query = `
        FOR d IN v_wiki_sorted
          SEARCH IN_RANGE(d.count, 99, 99999, true, true)
          OPTIONS { noMaterialization: @noMaterialization }
          SORT d._key
        RETURN { body: d.body, title: d.title }`;

      assertEqual(0, getNodes(query, "SortNode", doNotMaterialize).length);
      assertEqual(0, getNodes(query, "SortNode", materialize).length);

      let noMaterializationNode = getNodes(query, "EnumerateViewNode", doNotMaterialize)[0];
      assertNotUndefined(noMaterializationNode);
      assertTrue(noMaterializationNode.noMaterialization);
      assertEqual(["body","title"],
                  noMaterializationNode.viewValuesVars.map(v => v.field).sort());

      let node = getNodes(query, "EnumerateViewNode", materialize)[0];
      assertNotUndefined(node);
      assertFalse(node.noMaterialization);
      assertEqual(0, node.viewValuesVars.length);

      let expected = db._query(`
        FOR d IN wikipedia FILTER IN_RANGE(d.count, 99, 99999, true, true)
        SORT d._key
        RETURN { title: d.title, body: d.body }`, {}, noOptimization).toArray();
      assertNotEqual(expected.length, 0);

      let actual = db._query(query, doNotMaterialize).toArray().sort();
      assertEqual(expected.length, actual.length);
      actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));

      let actualEarlyMaterialization = db._query(query, materialize).toArray().sort();
      assertEqual(expected.length, actualEarlyMaterialization.length);
      actualEarlyMaterialization.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));
    },

    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure document isn't materialized
    /// 2. ensure arangosearch reads all values from ['invalidField'] column
    /// 3. ensure results are same as for collection with filter
    /// 4. ensure results are same as for view without stored values
    ////////////////////////////////////////////////////////////////////////////////
    testNoMaterializationForReturnNonExistentField: function () {
      let query = `
        FOR d IN v_wiki_stored 
          SEARCH IN_RANGE(d.count, 99, 99999, true, true)
          OPTIONS { noMaterialization: @noMaterialization }
        RETURN d.invalidField`;

      let noMaterializationNode = getNodes(query, "EnumerateViewNode", doNotMaterialize)[0];
      assertNotUndefined(noMaterializationNode);
      assertTrue(noMaterializationNode.noMaterialization);
      assertEqual(1, noMaterializationNode.viewValuesVars.length);
      let viewValues = noMaterializationNode.viewValuesVars[0];
      assertEqual(1, viewValues.viewStoredValuesVars.length);
      assertEqual("invalidField", viewValues.viewStoredValuesVars[0].field);

      let node = getNodes(query, "EnumerateViewNode", materialize)[0];
      assertNotUndefined(node);
      assertFalse(node.noMaterialization);
      assertEqual(0, node.viewValuesVars.length);

      let expected = db._query(`
        FOR d IN wikipedia FILTER IN_RANGE(d.count, 99, 99999, true, true)
        RETURN d.invalidField`, {}, noOptimization).toArray();
      assertNotEqual(expected.length, 0);
      expected.forEach(v => assertNull(v));

      let actual = db._query(query, doNotMaterialize).toArray();
      assertEqual(expected, actual);
      assertEqual(db._query(query, materialize).toArray(), actual);
    },

    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure document isn't materialized
    /// 2. ensure arangosearch reads all values from ["title", "created", "count", "_id"] column
    /// 3. ensure results are same as for collection with filter
    /// 4. ensure results are same as for view without stored values
    ////////////////////////////////////////////////////////////////////////////////
    testNoMaterializationForReturnMultipleValues: function () {
      let query = `
        FOR d IN v_wiki_stored
          SEARCH IN_RANGE(d.count, 99, 99999, true, true)
          OPTIONS { noMaterialization: @noMaterialization }
        RETURN { title:d.title, id: d._id, created:d.created }`;

      let noMaterializationNode = getNodes(query, "EnumerateViewNode", doNotMaterialize)[0];
      assertNotUndefined(noMaterializationNode);
      assertTrue(noMaterializationNode.noMaterialization);
      assertEqual(1, noMaterializationNode.viewValuesVars.length);
      let viewValues = noMaterializationNode.viewValuesVars[0];
      assertEqual(3, viewValues.viewStoredValuesVars.length);
      assertEqual(["_id","created","title"],
                  viewValues.viewStoredValuesVars.map(v => v.field).sort());
      let node = getNodes(query, "EnumerateViewNode", materialize)[0];
      assertNotUndefined(node);
      assertFalse(node.noMaterialization);
      assertEqual(0, node.viewValuesVars.length);

      let less = function(lhs, rhs) {
        if (lhs.id < rhs.id) {
          return -1;
        }
        if (lhs.id > rhs.id) {
          return 1;
        }
        return 0;
      };

      let expected = db._query(`
        FOR d IN wikipedia FILTER IN_RANGE(d.count, 99, 99999, true, true)
        RETURN { title:d.title, id: d._id, created:d.created }`, {}, noOptimization).toArray().sort(less);
      assertNotEqual(expected.length, 0);

      let actual = db._query(query, doNotMaterialize).toArray().sort(less);
      assertEqual(expected.length, actual.length);
      actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));

      let actualEarlyMaterialization = db._query(query, materialize).toArray().sort(less);
      assertEqual(expected.length, actualEarlyMaterialization.length);
      actualEarlyMaterialization.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));
    },

    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure document isn't materialized
    /// 2. ensure arangosearch reads all values from ['title'] column
    /// 3. ensure results are same as for collection with filter
    /// 4. ensure results are same as for view without stored values
    ////////////////////////////////////////////////////////////////////////////////
    testNoMaterializationForSort: function () {
      let query = `
        FOR d IN v_wiki_stored 
          SEARCH IN_RANGE(d.count, 99, 99999, true, true)
          OPTIONS { noMaterialization: @noMaterialization }
        SORT d.title
        RETURN d.title`;

      let noMaterializationNode = getNodes(query, "EnumerateViewNode", doNotMaterialize)[0];
      assertNotUndefined(noMaterializationNode);
      assertTrue(noMaterializationNode.noMaterialization);
      assertEqual(1, noMaterializationNode.viewValuesVars.length);
      let viewValues = noMaterializationNode.viewValuesVars[0];
      assertEqual(1, viewValues.viewStoredValuesVars.length);
      assertEqual("title", viewValues.viewStoredValuesVars[0].field);

      let node = getNodes(query, "EnumerateViewNode", materialize)[0];
      assertNotUndefined(node);
      assertFalse(node.noMaterialization);
      assertEqual(0, node.viewValuesVars.length);

      let expected = db._query(`
        FOR d IN wikipedia FILTER IN_RANGE(d.count, 99, 99999, true, true)
        SORT d.title
        RETURN d.title`, {}, noOptimization).toArray();
      assertNotEqual(expected.length, 0);

      let actual = db._query(query, doNotMaterialize).toArray();
      assertEqual(expected, actual);
      assertEqual(db._query(query, materialize).toArray(), actual);
    },

    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure document isn't materialized
    /// 2. ensure arangosearch reads all values from ['title'] column
    /// 3. ensure results are same as for collection with filter
    /// 4. ensure results are same as for view without stored values
    ////////////////////////////////////////////////////////////////////////////////
    testNoMaterializationForSortMultipleValues: function () {
      let query = `
        FOR d IN v_wiki_stored
          SEARCH IN_RANGE(d.count, 99, 99999, true, true)
          OPTIONS { noMaterialization: @noMaterialization }
        SORT d.title, d._id
        RETURN d.title`;

      let noMaterializationNode = getNodes(query, "EnumerateViewNode", doNotMaterialize)[0];
      assertNotUndefined(noMaterializationNode);
      assertTrue(noMaterializationNode.noMaterialization);
      assertEqual(1, noMaterializationNode.viewValuesVars.length);
      let viewValues = noMaterializationNode.viewValuesVars[0];
      assertEqual(2, viewValues.viewStoredValuesVars.length);
      assertEqual(["_id","title"],
                  viewValues.viewStoredValuesVars.map(v => v.field).sort());

      let node = getNodes(query, "EnumerateViewNode", materialize)[0];
      assertNotUndefined(node);
      assertFalse(node.noMaterialization);
      assertEqual(0, node.viewValuesVars.length);

      let expected = db._query(`
        FOR d IN wikipedia FILTER IN_RANGE(d.count, 99, 99999, true, true)
        SORT d.title, d._id
        RETURN d.title`, {}, noOptimization).toArray();
      assertNotEqual(expected.length, 0);

      let actual = db._query(query, doNotMaterialize).toArray();
      assertEqual(expected, actual);
      assertEqual(db._query(query, materialize).toArray(), actual);
    },

    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure document isn't materialized
    /// 2. ensure arangosearch reads all values from ['title'] column
    /// 3. ensure results are same as for collection with filter
    /// 4. ensure results are same as for view without stored values
    ////////////////////////////////////////////////////////////////////////////////
    testNoMaterializationForCollect: function () {
      let query = `
        FOR d IN v_wiki_stored
          SEARCH IN_RANGE(d.count, 99, 99999, true, true)
          OPTIONS { noMaterialization: @noMaterialization }
        COLLECT title = d.title WITH COUNT INTO count
        RETURN { title, count }`;

      let noMaterializationNode = getNodes(query, "EnumerateViewNode", doNotMaterialize)[0];
      assertNotUndefined(noMaterializationNode);
      assertTrue(noMaterializationNode.noMaterialization);
      assertEqual(1, noMaterializationNode.viewValuesVars.length);
      let viewValues = noMaterializationNode.viewValuesVars[0];
      assertEqual(1, viewValues.viewStoredValuesVars.length);
      assertEqual(["title"],
                  viewValues.viewStoredValuesVars.map(v => v.field).sort());

      let node = getNodes(query, "EnumerateViewNode", materialize)[0];
      assertNotUndefined(node);
      assertFalse(node.noMaterialization);
      assertEqual(0, node.viewValuesVars.length);

      let expected = db._query(`
        FOR d IN wikipedia FILTER IN_RANGE(d.count, 99, 99999, true, true)
        COLLECT title = d.title WITH COUNT INTO count
        RETURN { title, count }`, {}, noOptimization).toArray();
      assertNotEqual(expected.length, 0);

      let actual = db._query(query, doNotMaterialize).toArray();
      assertEqual(expected, actual);
      assertEqual(db._query(query, materialize).toArray(), actual);
    },

    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure document isn't materialized
    /// 2. ensure arangosearch reads all values from ["title", "created", "count", "_id"] column
    /// 3. ensure results are same as for collection with filter
    /// 4. ensure results are same as for view without stored values
    ////////////////////////////////////////////////////////////////////////////////
    testNoMaterializationForCollectAggregate: function () {
      let query = `
        FOR d IN v_wiki_stored
          SEARCH IN_RANGE(d.count, 99, 99999, true, true)
          OPTIONS { noMaterialization: @noMaterialization }
        COLLECT title = d.title 
          AGGREGATE max = MAX(d.count) 
          INTO groups = { count: d.count }
        RETURN { title, max, groups }`;

      let noMaterializationNode = getNodes(query, "EnumerateViewNode", doNotMaterialize)[0];
      assertNotUndefined(noMaterializationNode);
      assertTrue(noMaterializationNode.noMaterialization);
      assertEqual(1, noMaterializationNode.viewValuesVars.length);
      let viewValues = noMaterializationNode.viewValuesVars[0];
      assertEqual(2, viewValues.viewStoredValuesVars.length);
      assertEqual(["count", "title"],
                  viewValues.viewStoredValuesVars.map(v => v.field).sort());

      let node = getNodes(query, "EnumerateViewNode", materialize)[0];
      assertNotUndefined(node);
      assertFalse(node.noMaterialization);
      assertEqual(0, node.viewValuesVars.length);

      let less = function(lhs, rhs) {
        if (lhs.count < rhs.count) {
          return 1;
        }

        if (lhs.count > rhs.count) {
          return -1;
        }

        return 0;
      };

      let expected = db._query(`
        FOR d IN wikipedia FILTER IN_RANGE(d.count, 99, 99999, true, true)
        COLLECT title = d.title 
          AGGREGATE max = MAX(d.count) 
          INTO groups = { count: d.count }
        RETURN { title, max, groups }`, {}, noOptimization).toArray();
      expected.forEach(v => v.groups.sort(less));
      assertNotEqual(expected.length, 0);

      let actual = db._query(query, doNotMaterialize).toArray();
      actual.forEach(v => v.groups.sort(less));
      assertEqual(expected.length, actual.length);
      actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));

      let actualEarlyMaterialization = db._query(query, materialize).toArray();
      actualEarlyMaterialization.forEach(v => v.groups = v.groups.sort(less));
      assertEqual(expected.length, actualEarlyMaterialization.length);
      actualEarlyMaterialization.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));
    },

    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure document isn't materialized
    /// 2. ensure arangosearch reads all values from ["title", "created", "count", "_id"] column
    /// 3. ensure results are same as for collection with filter
    /// 4. ensure results are same as for view without stored values
    ////////////////////////////////////////////////////////////////////////////////
    testNoMaterializationForTraversal: function () {
      let query = `
        FOR d IN v_wiki_stored
          SEARCH IN_RANGE(d.count, 99, 99999, true, true)
          OPTIONS { noMaterialization: @noMaterialization }
            FOR v,e,p IN 1..2 OUTBOUND d._id links
        RETURN p`;

      let noMaterializationNode = getNodes(query, "EnumerateViewNode", doNotMaterialize)[0];
      assertNotUndefined(noMaterializationNode);
      assertTrue(noMaterializationNode.noMaterialization);
      assertEqual(1, noMaterializationNode.viewValuesVars.length);
      let viewValues = noMaterializationNode.viewValuesVars[0];
      assertEqual(1, viewValues.viewStoredValuesVars.length);
      assertEqual(["_id"],
                  viewValues.viewStoredValuesVars.map(v => v.field).sort());

      let node = getNodes(query, "EnumerateViewNode", materialize)[0];
      assertNotUndefined(node);
      assertFalse(node.noMaterialization);
      assertEqual(0, node.viewValuesVars.length);

      let expected = db._query(`
        FOR d IN wikipedia FILTER IN_RANGE(d.count, 99, 99999, true, true)
          FOR v,e,p IN 1..2 OUTBOUND d._id links
        RETURN p`, {}, noOptimization).toArray();
      assertNotEqual(expected.length, 0);

      let actual = db._query(query, doNotMaterialize).toArray();
      assertEqual(expected, actual);
      assertEqual(db._query(query, materialize).toArray(), actual);
    },

    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure document isn't materialized
    /// 2. ensure arangosearch reads all values from ["title", "created", "count", "_id"]
    ///    and primarySort columns
    /// 3. ensure results are same as for collection with filter
    /// 4. ensure results are same as for view without stored values
    ////////////////////////////////////////////////////////////////////////////////
    testNoMaterializationForJoinWithView0: function () {
      let query = `
        FOR d IN v_wiki_stored
          SEARCH IN_RANGE(d.count, 99, 9999, true, true)
          OPTIONS { noMaterialization: @noMaterialization }
            FOR j IN v_wiki_sorted
              SEARCH IN_RANGE(j.count, 99, 9999, true, true) AND j._id == d._id
              OPTIONS { noMaterialization: @noMaterialization }
          SORT j._key
        RETURN { body: j.body, key: j._key, title: d.title }`;

      {
        let viewNodes = getNodes(query, "EnumerateViewNode", doNotMaterialize)
        assertEqual(2, viewNodes.length);

        let viewWithStoredValues = viewNodes.find(v => v.view === "v_wiki_stored");
        assertNotUndefined(viewWithStoredValues);
        assertTrue(viewWithStoredValues.noMaterialization);
        assertEqual(1, viewWithStoredValues.viewValuesVars.length);
        assertEqual(["_id", "title"],
                    viewWithStoredValues.viewValuesVars[0].viewStoredValuesVars.map(v => v.field).sort());

        let viewWithSortedValues = viewNodes.find(v => v.view === "v_wiki_sorted");
        assertNotUndefined(viewWithSortedValues);
        assertTrue(viewWithSortedValues.noMaterialization);
        assertEqual(2, viewWithSortedValues.viewValuesVars.length);
        assertEqual(["_key", "body"],
                    viewWithSortedValues.viewValuesVars.map(v => v.field).sort());
      }

      {
        let viewNodes = getNodes(query, "EnumerateViewNode", materialize);
        assertEqual(2, viewNodes.length);
        assertFalse(viewNodes[0].noMaterialization);
        assertEqual(0, viewNodes[0].viewValuesVars.length);
        assertFalse(viewNodes[1].noMaterialization);
        assertEqual(0, viewNodes[1].viewValuesVars.length);
      }

      let expected = db._query(`
        FOR d IN wikipedia FILTER IN_RANGE(d.count, 99, 9999, true, true)
        SORT d._key
        RETURN { body: d.body, title: d.title, key: d._key }`, {}, noOptimization).toArray();
      assertNotEqual(expected.length, 0);

      let actual = db._query(query, doNotMaterialize).toArray();
      assertEqual(expected.length, actual.length);
      actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));

      let actualEarlyMaterialization = db._query(query, materialize).toArray();
      assertEqual(expected.length, actualEarlyMaterialization.length);
      actualEarlyMaterialization.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));
    },

    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure document isn't materialized
    /// 2. ensure arangosearch reads all values from ["title", "created", "count", "_id"]
    ///    and primarySort columns
    /// 3. ensure results are same as for collection with filter
    /// 4. ensure results are same as for view without stored values
    ////////////////////////////////////////////////////////////////////////////////
    testNoMaterializationForJoinWithView1: function () {
      let query = `
        FOR d IN v_wiki_stored
          SEARCH IN_RANGE(d.count, 99, 9999, true, true)
          OPTIONS { noMaterialization: @noMaterialization }
            LET id = NOOPT(d._id)
            FOR j IN v_wiki_sorted
              SEARCH IN_RANGE(j.count, 99, 9999, true, true) AND j._id == id
              OPTIONS { noMaterialization: @noMaterialization }
          SORT j._key
        RETURN { body: j.body, key: j._key, title: d.title }`;

      {
        let viewNodes = getNodes(query, "EnumerateViewNode", doNotMaterialize)
        assertEqual(2, viewNodes.length);

        let viewWithStoredValues = viewNodes.find(v => v.view === "v_wiki_stored");
        assertNotUndefined(viewWithStoredValues);
        assertTrue(viewWithStoredValues.noMaterialization);
        assertEqual(1, viewWithStoredValues.viewValuesVars.length);
        assertEqual(["_id", "title"],
                    viewWithStoredValues.viewValuesVars[0].viewStoredValuesVars.map(v => v.field).sort());

        let viewWithSortedValues = viewNodes.find(v => v.view === "v_wiki_sorted");
        assertNotUndefined(viewWithSortedValues);
        assertTrue(viewWithSortedValues.noMaterialization);
        assertEqual(2, viewWithSortedValues.viewValuesVars.length);
        assertEqual(["_key", "body"],
                    viewWithSortedValues.viewValuesVars.map(v => v.field).sort());
      }

      {
        let viewNodes = getNodes(query, "EnumerateViewNode", materialize);
        assertEqual(2, viewNodes.length);
        assertFalse(viewNodes[0].noMaterialization);
        assertEqual(0, viewNodes[0].viewValuesVars.length);
        assertFalse(viewNodes[1].noMaterialization);
        assertEqual(0, viewNodes[1].viewValuesVars.length);
      }

      let expected = db._query(`
        FOR d IN wikipedia FILTER IN_RANGE(d.count, 99, 9999, true, true)
        SORT d._key
        RETURN { body: d.body, title: d.title, key: d._key }`, {}, noOptimization).toArray();
      assertNotEqual(expected.length, 0);

      let actual = db._query(query, doNotMaterialize).toArray();
      assertEqual(expected.length, actual.length);
      actual.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));

      let actualEarlyMaterialization = db._query(query, materialize).toArray();
      assertEqual(expected.length, actualEarlyMaterialization.length);
      actualEarlyMaterialization.forEach((rhs, i) => assertTrue(_.isEqual(expected[i],rhs)));
    },

    ////////////////////////////////////////////////////////////////////////////////
    /// 1. ensure document isn't materialized
    /// 2. ensure arangosearch reads all values from ["title", "created", "count", "_id"] column
    /// 3. ensure results are same as for collection with filter
    /// 4. ensure results are same as for view without stored values
    ////////////////////////////////////////////////////////////////////////////////
    testNoMaterializationForJoinWithIndex: function () {
      let query = `
        FOR d IN v_wiki_stored
          SEARCH IN_RANGE(d.count, 99, 99999, true, true)
          OPTIONS { noMaterialization: @noMaterialization }
            FOR j IN wikipedia FILTER j._id == d._id
        RETURN j.title`;

      let noMaterializationNode = getNodes(query, "EnumerateViewNode", doNotMaterialize)[0];
      assertNotUndefined(noMaterializationNode);
      assertTrue(noMaterializationNode.noMaterialization);
      assertEqual(1, noMaterializationNode.viewValuesVars.length);
      let viewValues = noMaterializationNode.viewValuesVars[0];
      assertEqual(2, viewValues.viewStoredValuesVars.length);
      assertEqual(["_id"],
                  viewValues.viewStoredValuesVars.map(v => v.field).sort());

      let node = getNodes(query, "EnumerateViewNode", materialize)[0];
      assertNotUndefined(node);
      assertFalse(node.noMaterialization);
      assertEqual(0, node.viewValuesVars.length);

      let expected = db._query(`
        FOR d IN wikipedia FILTER IN_RANGE(d.count, 99, 99999, true, true)
        RETURN d.title`, {}, noOptimization).toArray();
      assertNotEqual(expected.length, 0);

      let actual = db._query(query, doNotMaterialize).toArray();
      assertEqual(expected, actual);
      assertEqual(db._query(query, materialize).toArray(), actual);
    },
  };
}

////////////////////////////////////////////////////////////////////////////////
/// @brief executes the test suite
////////////////////////////////////////////////////////////////////////////////

jsunity.run(ArangoSearch_StoredValues);
if (false === jsunity.done().status) {
  throw "fail";
}
