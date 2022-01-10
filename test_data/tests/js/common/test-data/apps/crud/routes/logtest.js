'use strict';
const dd = require('dedent');
const joi = require('joi');
const httpError = require('http-errors');
const status = require('statuses');
const errors = require('@arangodb').errors;
const createRouter = require('@arangodb/foxx/router');
const Logtest = require('../models/logtest');

const logtestItems = module.context.collection('logtest');
const keySchema = joi.string().required()
.description('The key of the logtest');

const ARANGO_NOT_FOUND = errors.ERROR_ARANGO_DOCUMENT_NOT_FOUND.code;
const ARANGO_DUPLICATE = errors.ERROR_ARANGO_UNIQUE_CONSTRAINT_VIOLATED.code;
const ARANGO_CONFLICT = errors.ERROR_ARANGO_CONFLICT.code;
const HTTP_NOT_FOUND = status('not found');
const HTTP_CONFLICT = status('conflict');

const router = createRouter();
module.exports = router;


router.tag('logtest');


router.get(function (req, res) {
  res.send(logtestItems.all());
}, 'list')
.response([Logtest], 'A list of logtestItems.')
.summary('List all logtestItems')
.description(dd`
  Retrieves a list of all logtestItems.
`);


router.post(function (req, res) {
  const logtest = req.body;
  let meta;
  try {
     console.log(logtest);
  } catch (e) {
    if (e.isArangoError && e.errorNum === ARANGO_DUPLICATE) {
      throw httpError(HTTP_CONFLICT, e.message);
    }
    throw e;
  }
  res.status(201);
  res.send(logtest);
}, 'log')
.body(Logtest, 'The logtest to log.')
.response(201, Logtest, 'The created logtest.')
.summary('log an item')
.description(dd`
  logs request body.
`);


router.get(':key', function (req, res) {
  const key = req.pathParams.key;
  let logtest
  try {
    logtest = logtestItems.document(key);
  } catch (e) {
    if (e.isArangoError && e.errorNum === ARANGO_NOT_FOUND) {
      throw httpError(HTTP_NOT_FOUND, e.message);
    }
    throw e;
  }
  res.send(logtest);
}, 'detail')
.pathParam('key', keySchema)
.response(Logtest, 'The logtest.')
.summary('Fetch a logtest')
.description(dd`
  Retrieves a logtest by its key.
`);


router.put(':key', function (req, res) {
  const key = req.pathParams.key;
  const logtest = req.body;
  let meta;
  try {
    meta = logtestItems.replace(key, logtest);
  } catch (e) {
    if (e.isArangoError && e.errorNum === ARANGO_NOT_FOUND) {
      throw httpError(HTTP_NOT_FOUND, e.message);
    }
    if (e.isArangoError && e.errorNum === ARANGO_CONFLICT) {
      throw httpError(HTTP_CONFLICT, e.message);
    }
    throw e;
  }
  Object.assign(logtest, meta);
  res.send(logtest);
}, 'replace')
.pathParam('key', keySchema)
.body(Logtest, 'The data to replace the logtest with.')
.response(Logtest, 'The new logtest.')
.summary('Replace a logtest')
.description(dd`
  Replaces an existing logtest with the request body and
  returns the new document.
`);


router.patch(':key', function (req, res) {
  const key = req.pathParams.key;
  const patchData = req.body;
  let logtest;
  try {
    logtestItems.update(key, patchData);
    logtest = logtestItems.document(key);
  } catch (e) {
    if (e.isArangoError && e.errorNum === ARANGO_NOT_FOUND) {
      throw httpError(HTTP_NOT_FOUND, e.message);
    }
    if (e.isArangoError && e.errorNum === ARANGO_CONFLICT) {
      throw httpError(HTTP_CONFLICT, e.message);
    }
    throw e;
  }
  res.send(logtest);
}, 'update')
.pathParam('key', keySchema)
.body(joi.object().description('The data to update the logtest with.'))
.response(Logtest, 'The updated logtest.')
.summary('Update a logtest')
.description(dd`
  Patches a logtest with the request body and
  returns the updated document.
`);


router.delete(':key', function (req, res) {
  const key = req.pathParams.key;
  try {
    logtestItems.remove(key);
  } catch (e) {
    if (e.isArangoError && e.errorNum === ARANGO_NOT_FOUND) {
      throw httpError(HTTP_NOT_FOUND, e.message);
    }
    throw e;
  }
}, 'delete')
.pathParam('key', keySchema)
.response(null)
.summary('Remove a logtest')
.description(dd`
  Deletes a logtest from the database.
`);
