/* global print, ARGUMENTS */
//

function isCharDigit(n){
  return !!n.trim() && n > -1;
}

function scanMakeDataPaths (options, PWD, oldVersion, newVersion, wantFunctions, nameString) {
  let fns = [[],[]];
  const FNChars = [ 'D', 'L'];
  let filters = [];
  if (options.hasOwnProperty('test') && (typeof (options.test) !== 'undefined')) {
    filters = options.test.split(',');
  }
  let suites = _.filter(
    fs.list(fs.join(PWD, 'makedata_suites')),
    function (p) {
      if (!isCharDigit(p.charAt(0))) {
        return false;
      }
      if (filters.length > 0) {
        let found = false;
        filters.forEach(flt => {
          if (p.search(flt) >= 0) {
            found = true;
          }
        });
        if (!found) {
          return false;
        }
      }
      return (p.substr(-3) === '.js');
    }).map(function (x) {
      return fs.join(fs.join(PWD, 'makedata_suites'), x);
    }).sort();
  suites.forEach(suitePath => {
    let supported = "";
    let unsupported = "";
    let suite = require("internal").load(suitePath);
    if (suite.isSupported(oldVersion, newVersion, options, enterprise, isCluster)) {
      let count = 0;
      wantFunctions.forEach(fn => {
        if (wantFunctions[count] in suite) {
          supported += FNChars[count];
          fns[count].push(suite[fn]);
        } else {
          unsupported += " ";
        }
        count += 1;
      })
    } else {
      supported = " ";
      unsupported = " ";
    }
    print("[" + supported +"]   " + unsupported + suitePath);
  });
  return fns;
}

function mainTestLoop(options, isCluster, enterprise, fns, endOfLoopFN) {
  let dbCount = 0;
  while (dbCount < options.numberOfDBs) {
    tStart = time();
    timeLine = [tStart];
    fns[0].forEach(func => {
      db._useDatabase("_system");
      func(options,
           isCluster,
           enterprise,
           database,
           dbCount);
    });

    let loopCount = options.collectionCountOffset;
    while (loopCount < options.collectionMultiplier) {
      progress();
      fns[1].forEach(func => {
        func(options,
             isCluster,
             enterprise,
             dbCount,
             loopCount);
      });

      progress();
      loopCount ++;
    }
    progress();

    endOfLoopFN(database);
    print(timeLine.join());
    dbCount++;
  }
}

function getMetricValue (text, name) {
  let re = new RegExp("^" + name);
  let matches = text.split('\n').filter((line) => !line.match(/^#/)).filter((line) => line.match(re));
  if (!matches.length) {
    throw "Metric " + name + " not found";
  }
  return Number(matches[0].replace(/^.*{.*}([0-9.]+)$/, "$1"));
}

exports.scanMakeDataPaths = scanMakeDataPaths;
exports.mainTestLoop = mainTestLoop;
exports.getMetricValue = getMetricValue;
