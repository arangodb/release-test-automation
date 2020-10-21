/* jshint globalstrict:false, unused:false */
/* global print, start_pretty_print, ARGUMENTS */
'use strict';

const _ = require('lodash');
const internal = require('internal');
const platform = internal.platform;

const makeDirectoryRecursive = require('fs').makeDirectoryRecursive;
const killRemainingProcesses = require('@arangodb/process-utils').killRemainingProcesses;
const SetGlobalExecutionDeadlineTo = require('internal').SetGlobalExecutionDeadlineTo;
const inspect = internal.inspect;

const optionsDefaults = {
  'dumpAgencyOnError': false,
  'agencySize': 3,
  'agencyWaitForSync': false,
  'agencySupervision': true,
  'build': '',
  'buildType': (platform.substr(0, 3) === 'win') ? 'RelWithDebInfo':'',
  'cleanup': true,
  'cluster': false,
  'concurrency': 3,
  'configDir': 'etc/testing',
  'coordinators': 1,
  'coreCheck': false,
  'coreDirectory': '/var/tmp',
  'dbServers': 2,
  'duration': 10,
  'extraArgs': {},
  'extremeVerbosity': false,
  'force': true,
  'forceJson': false,
  'getSockStat': false,
  'arangosearch':true,
  'loopEternal': false,
  'loopSleepSec': 1,
  'loopSleepWhen': 1,
  'minPort': 1024,
  'maxPort': 32768,
  'onlyNightly': false,
  'password': '',
  'protocol': 'tcp',
  'replication': false,
  'rr': false,
  'exceptionFilter': null,
  'exceptionCount': 1,
  'sanitizer': false,
  'activefailover': false,
  'singles': 2,
  'sniff': false,
  'sniffAgency': true,
  'sniffDBServers': true,
  'sniffDevice': undefined,
  'sniffProgram': undefined,
  'skipLogAnalysis': true,
  'skipMemoryIntense': false,
  'skipNightly': true,
  'skipNondeterministic': false,
  'skipGrey': false,
  'onlyGrey': false,
  'oneTestTimeout': 15 * 60,
  'isAsan': false,
  'skipTimeCritical': false,
  'storageEngine': 'rocksdb',
  'test': undefined,
  'testBuckets': undefined,
  'testOutputDirectory': 'out',
  'useReconnect': true,
  'username': 'root',
  'valgrind': false,
  'valgrindFileBase': '',
  'valgrindArgs': {},
  'valgrindHosts': false,
  'verbose': false,
  'vst': false,
  'http2': false,
  'walFlushTimeout': 30000,
  'writeXmlReport': false,
  'testFailureText': 'testfailures.txt',
  'crashAnalysisText': 'testfailures.txt',
  'testCase': undefined,
  'disableMonitor': false,
  'disableClusterMonitor': true,
  'sleepBeforeStart' : 0,
  'sleepBeforeShutdown' : 0,
  'instanceInfo' : {}
};

// //////////////////////////////////////////////////////////////////////////////
// / @brief runs a local unittest file in the current arangosh
// //////////////////////////////////////////////////////////////////////////////

function runInLocalArangosh (options, instanceInfo, file, addArgs) {
  let endpoint = arango.getEndpoint();
  if (options.vst || options.http2) {
    let newEndpoint = findEndpoint(options, instanceInfo);
    if (endpoint !== newEndpoint) {
      print(`runInLocalArangosh: Reconnecting to ${newEndpoint} from ${endpoint}`);
      arango.reconnect(newEndpoint, '_system', 'root', '');
    }
  }
  
  let testCode;
  // \n's in testCode are required because of content could contain '//' at the very EOF
  if (file.indexOf('-spec') === -1) {
    let testCase = JSON.stringify(options.testCase);
    if (options.testCase === undefined) {
      testCase = '"undefined"';
    }
    testCode = 'const runTest = require("jsunity").runTest;\n ' +
      'return runTest(' + JSON.stringify(file) + ', true, ' + testCase + ');\n';
  } else {
    let mochaGrep = options.testCase ? ', ' + JSON.stringify(options.testCase) : '';
    testCode = 'const runTest = require("@arangodb/mocha-runner"); ' +
      'return runTest(' + JSON.stringify(file) + ', true' + mochaGrep + ');\n';
  }
  require('internal').env.INSTANCEINFO = JSON.stringify(instanceInfo);
  let testFunc;
  eval('testFunc = function () { \nglobal.instanceInfo = ' + JSON.stringify(instanceInfo) + ';\n' + testCode + "}");
  
  try {
    SetGlobalExecutionDeadlineTo(options.oneTestTimeout * 1000);
    let result = testFunc();
    let timeout = SetGlobalExecutionDeadlineTo(0.0);
    if (timeout) {
      return {
        timeout: true,
        forceTerminate: true,
        status: false,
        message: "test ran into timeout. Original test status: " + JSON.stringify(result),
      };
    }
    return result;
  } catch (ex) {
    let timeout = SetGlobalExecutionDeadlineTo(0.0);
    return {
      timeout: timeout,
      forceTerminate: true,
      status: false,
      message: "test has thrown! '" + file + "' - " + ex.message || String(ex),
      stack: ex.stack
    };
  }
}
runInLocalArangosh.info = 'runInLocalArangosh';





// //////////////////////////////////////////////////////////////////////////////
//  @brief runs the test using the test facilities in js/client/modules/@arangodb
// //////////////////////////////////////////////////////////////////////////////

function main (argv) {
  start_pretty_print();

  let testCases = []; // e.g all, http_server, recovery, ...
  let options = {};

  while (argv.length >= 1) {
    if (argv[0].slice(0, 1) === '-') { // break parsing if we hit some -option
      break;
    }

    testCases.push(argv[0]); // append first arg to test suits
    argv = argv.slice(1);    // and remove first arg (c++:pop_front/bash:shift)
  }

  if (argv.length >= 1) {
    try {
      options = internal.parseArgv(argv, 0);
    } catch (x) {
      print('failed to parse the options: ' + x.message + '\n' + String(x.stack));
      print('argv: ', argv);
      throw x;
    }
  }

  if (options.hasOwnProperty('testOutput')) {
    options.testOutputDirectory = options.testOutput + '/';
  }
  _.defaults(options, optionsDefaults);

  // create output directory
  try {
    makeDirectoryRecursive(options.testOutputDirectory);
  } catch (x) {
    print("failed to create test directory - " + x.message);
    throw x;
  }

  let result = {
    status: true,
    crashed: false
  };
  try {
    testCases.forEach(function(testCase) {
      result[testCase] = 
        runInLocalArangosh (options, options.instanceInfo, testCase, {});
      result.status &= result[testCase].hasOwnProperty('status') && result[testCase].status;
    });
  } catch (x) {
    if (x.message === "USAGE ERROR") {
      throw x;
    }
    print('caught exception during test execution!');

    if (x.message !== undefined) {
      print(x.message);
    }

    if (x.stack !== undefined) {
      print(x.stack);
    } else {
      print(x);
    }

    print(JSON.stringify(result));
    throw x;
  }
  
  _.defaults(result, {
    status: false,
    crashed: true
  });
  print(result)
  killRemainingProcesses(result);


  return result.status;
}

let result = main(ARGUMENTS);

if (!result) {
  // force an error in the console
  process.exit(1);
}

