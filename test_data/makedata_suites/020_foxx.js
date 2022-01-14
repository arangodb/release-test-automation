// inspired by shell-foxx-api-spec.js
function loadFoxxIntoZip(path) {
  let zip = utils.zipDirectory(path);
  let content = fs.readFileSync(zip);
  fs.remove(zip);
  return {
    type: 'inlinezip',
    buffer: content
  };
}

function installFoxx(mountpoint, which, mode) {
  let headers = {};
  let content;
  if (which.type === 'js') {
    headers['content-type'] = 'application/javascript';
    content = which.buffer;
  } else if (which.type === 'dir') {
    headers['content-type'] = 'application/zip';
    var utils = require('@arangodb/foxx/manager-utils');
    let zip = utils.zipDirectory(which.buffer);
    content = fs.readFileSync(zip);
    fs.remove(zip);
  } else if (which.type === 'inlinezip') {
    content = which.buffer;
    headers['content-type'] = 'application/zip';
  } else if (which.type === 'url') {
    content = { source: which };
  } else if (which.type === 'file') {
    content = fs.readFileSync(which.buffer);
  }
  let devmode = '';
  if (typeof which.devmode === "boolean") {
    devmode = `&development=${which.devmode}`;
  }
  let crudResp;
  if (mode === "upgrade") {
    crudResp = arango.PATCH('/_api/foxx/service?mount=' + mountpoint + devmode, content, headers);
  } else if (mode === "replace") {
    crudResp = arango.PUT('/_api/foxx/service?mount=' + mountpoint + devmode, content, headers);
  } else {
    let reply = download(
      arango.getEndpoint().replace(/^tcp:/, 'http:').replace(/^ssl:/, 'https:') +
        '/_api/foxx?mount=' + mountpoint + devmode,
      content,
      {
        method: 'POST',
        headers: headers,
        timeout: 300,
        username: 'root',
        password: options.passvoid,
      });
    expect(reply.code).to.equal(201);
    crudResp = JSON.parse(reply.body);
  }
  expect(crudResp).to.have.property('manifest');
  return crudResp;
}

function deleteFoxx(mountpoint) {
  const deleteResp = arango.DELETE('/_api/foxx/service?force=true&mount=' + mountpoint);
  expect(deleteResp).to.have.property('code');
  expect(deleteResp.code).to.equal(204);
  expect(deleteResp.error).to.equal(false);
}

const itzpapalotlPath = path.resolve(internal.pathForTesting('common'), 'test-data', 'apps', 'itzpapalotl');
const itzpapalotlZip = loadFoxxIntoZip(itzpapalotlPath);
const minimalWorkingServicePath = path.resolve(internal.pathForTesting('common'), 'test-data', 'apps', 'crud');
const minimalWorkingZip = loadFoxxIntoZip(minimalWorkingServicePath);
const minimalWorkingZipDev = {
  buffer: minimalWorkingZip.buffer,
  devmode: true,
  type: minimalWorkingZip.type
};
const minimalWorkingZipPath = utils.zipDirectory(minimalWorkingServicePath);

const serviceServicePath = path.resolve(internal.pathForTesting('common'), 'test-data', 'apps', 'service-service', 'index.js');
const crudTestServiceSource = {
  type: 'js',
  buffer: fs.readFileSync(serviceServicePath)
};
function checkFoxxService() {
}


(function () {
  let shouldValidateFoxx;
  return {
    isSupported: function(version, oldVersion, options, enterprise, cluster) {
      return (options.numberOfDBs === 1 && options.collectionMultiplier === 1 && options.testFoxx);
    },

    makeDataDB: function(options, isCluster, isEnterprise, database, dbCount) {
      // All items created must contain dbCount
      print(`making per database data ${dbCount}`);
      print("installing Itzpapalotl");
      installFoxx('/itz', itzpapalotlZip);

      print("installing crud");
      installFoxx('/crud', minimalWorkingZip);
    },
    makeData: function(options, isCluster, isEnterprise, dbCount, loopCount) {
      // All items created must contain dbCount and loopCount
      print(`making data ${dbCount} ${loopCount}`);
    },
    checkDataDB: function(options, isCluster, isEnterprise, dbCount,  readOnly) {
      print(`checking data ${dbConut} `);
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
        for (let i=0; i < 200; i++) {
          try {
            reply = arango.GET_RAW(route, onlyJson);
            if (reply.code === 200) {
              print(route + " OK");
              return;
            }
            let msg = JSON.stringify(reply);
            if (reply.hasOwnProperty('parsedBody')) {
              msg = " '" + reply.parsedBody.errorNum + "' - " + reply.parsedBody.errorMessage;
            }
            print(route + " Not yet ready, retrying: " + msg);
          } catch (e) {
            print(route + " Caught - need to retry. " + JSON.stringify(e));
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
      
      reply = arango.POST_RAW('/_db/_system/crud/xxx', {_key: "test"});
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

      print('Foxx: crud testing delete document');
      reply = arango.DELETE_RAW('/_db/_system/crud/xxx/' + 'test');
      if (options.readOnly) {
        assertEqual(reply.code, "400");
      } else {
        assertEqual(reply.code, "204");
      }
    }
  };

}())
