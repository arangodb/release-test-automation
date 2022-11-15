/* global print, ARGUMENTS */
//

function scanMakeDataPaths (options, PWD, oldVersion, newVersion, wantFunctions, nameString) {
  let fns = [[],[]];
  const FNChars = [ 'D', 'L'];
  let suites = _.filter(
    fs.list(fs.join(PWD, 'makedata_suites')),
    function (p) {
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


exports.scanMakeDataPaths = scanMakeDataPaths;
exports.mainTestLoop = mainTestLoop;
