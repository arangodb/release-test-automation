/* global fs, PWD, writeGraphData, getShardCount, getReplicationFactor,  print, progress, db, createSafe, _, semver */

(function () {
    let sgm;

    const numberOfShards = 7;
    const verticesInSatellite = 13;

    const generateNames = (loopCount, isDisjoint) => {
        const disjointPostfix = isDisjoint ? "_disjoint" : "";
        return {
            smartGraphName: `UnitTestHybridSmartGraph_${loopCount}${disjointPostfix}`,
            satelliteCollectionName: `UnitTestSmartSat_${loopCount}${disjointPostfix}`,
            verticesCollectionName: `UnitTestSmartVertices_${loopCount}${disjointPostfix}`,
            edgesCollectionName: `UnitTestSmartEdges_${loopCount}${disjointPostfix}`,
            edgesSatToSatCollectionName: `UnitTestSatToSatEdges_${loopCount}${disjointPostfix}`,
            edgesSatToSmartCollectionName: `UnitTestSatToSmartEdges_${loopCount}${disjointPostfix}`,
            edgesSmartToSatCollectionName: `UnitTestSmartToSatEdges_${loopCount}${disjointPostfix}`,
            smartGraphAttribute: `smart_${loopCount}${disjointPostfix}`
        };
    };

    const createGraph = (isDisjoint, loopCount) => {
        const {
            smartGraphName,
            satelliteCollectionName,
            verticesCollectionName,
            edgesCollectionName,
            edgesSatToSatCollectionName,
            edgesSatToSmartCollectionName,
            edgesSmartToSatCollectionName,
            smartGraphAttribute
        } =  generateNames(loopCount, isDisjoint);
        let options = {
            satellites: [satelliteCollectionName],
            isDisjoint,
            smartGraphAttribute,
            isSmart: true,
            numberOfShards,
            replicationFactor: 2
        };
        const edgeDefinitions = [
            sgm._relation(
                edgesCollectionName,
                verticesCollectionName,
                verticesCollectionName
            ),
            sgm._relation(
                edgesSatToSatCollectionName,
                satelliteCollectionName,
                satelliteCollectionName
            ),
            sgm._relation(
                edgesSmartToSatCollectionName,
                verticesCollectionName,
                satelliteCollectionName
            ),
            sgm._relation(
                edgesSatToSmartCollectionName,
                satelliteCollectionName,
                verticesCollectionName
            )
        ];
        // Create a Hybrid Smart Graph
        return createSafe(smartGraphName, graphName => {
            return sgm._create(graphName, edgeDefinitions, [], options);

        }, graphName => {
            return sgm._graph(graphName);
        });
    };

    const generateSmartGraphShardKeys = (collection) => {
        const shardToKeyMap = {};
        let i = 0;
        while (Object.keys(shardToKeyMap).length < numberOfShards) {
            const smartKey = `smart${i}`;
            const doc = {
                _key: `${smartKey}:abc`
            };
            const shard = collection.getResponsibleShard(doc);
            // We assume that eventually every shard will be hit by this loop once
            // We cannot assert on the shardKey value itself, we can only assert on the
            // number of documents per shard.
            shardToKeyMap[shard] = smartKey;
            ++i;
        }
        // Let us transform the mapping, such that we and up with a flat array of the values.
        // Which is sorted by the shardNames.
        // [<keyForShard0>,<keyForShard1>, ....];
        const shards = Object.keys(shardToKeyMap).sort();
        const shardKeys = [];
        for (const s of shards) {
            shardKeys.push(shardToKeyMap[s]);
        }
        return shardKeys;
    }

    // @brief helper method to define how many documents should be inserted into which shard
    // This method is deterministic by alphabetical ordering of shards, and should yield a different amount
    // of documents per shard, such that we can reliable count on source and target data-center
    const expectedNumberOfDocuments = (shardList) => {
        const res = {};
        shardList.sort().forEach((s,index) => res[s] = (index + 1) * 2);
        return res;
    };


    /// @brief, helper method to create Smart-sharded documents.
    /// Will create expectedNumberOfDocuments vertices in every respective shard.
    const createSmartVertices = (collection, shardKeys, smartGraphAttribute) => {
        const shardList = collection.shards().sort();
        const numDocs = expectedNumberOfDocuments(shardList);
        const docs = [];
        for (let i = 0; i < shardList.length; ++i) {
            const shardKey = shardKeys[i];
            // Insert expected NumberOfDocuments many documents into each different shardkey.
            for (let c = 0; c < numDocs[shardList[i]]; ++c) {
                docs.push({[smartGraphAttribute]: shardKey});
            }
        }
        collection.save(docs);
        progress(`Created Smart Vertices`);
    };

    /// @brief, helper method to create satellite documents.
    /// Will create verticesInSatellite many documents inside the Satellite collection
    const createSatelliteVertices = (collection) => {
        const shardList = collection.shards().sort();
        if (shardList.length !== 1) {
            throw new Error(`Satellite Collection "${collection.name()}" has more than 1 shard`);
        }
        const docs = [];
        for (let i = 0; i < verticesInSatellite; ++i) {
            docs.push({value: i});
        }
        collection.save(docs);
        progress(`Created Satellite Vertices`);
    };

    /// @brief, helper method to create satellite->satellite edges.
    /// Will create verticesInSatellite many edges inside the Satellite->Satellite collection
    const createSatToSatEdges = (collection, fromCol, toCol) => {
        const shardList = collection.shards().sort();
        if (shardList.length !== 1) {
            throw new Error(`Satellite Edge Collection "${collection.name()}" has more than 1 shard`);
        }
        const docs = [];
        for (let i = 0; i < verticesInSatellite; ++i) {
            docs.push({_from: `${fromCol}/abc`, _to: `${toCol}/abc`});
        }
        collection.save(docs);
        progress(`Created Satellite Vertices`);
    };

    const testSmartVerticesExist = (collection) => {
        progress(`Testing, Smart Vertex Collection document counts`);
        const shardList = collection.shards().sort();
        const numDocs = expectedNumberOfDocuments(shardList);
        const counts = collection.count(true);
        for (const shard of shardList) {
            if (counts[shard] !== numDocs[shard]) {
                throw new Error(`Mismatching counts on Smart Vertex shard ${shard}, got ${counts[shard]} vs. ${numDocs[shard]}`);
            }
        }
        progress(`Success, Smart Vertex Collection document counts match`);
    };

    const testSatelliteVerticesExist = (collection) => {
        progress(`Testing, Satellite Vertex Collection document counts`);
        const shardList = collection.shards().sort();
        if (shardList.length !== 1) {
            throw new Error(`Satellite Collection "${collection.name()}" has more than 1 shard`);
        }
        const counts = collection.count(true);
        for (const shard of shardList) {
            if (counts[shard] !== verticesInSatellite) {
                throw new Error(`Mismatching counts on Satellite Vertex shard ${shard}, got ${counts[shard]} vs. ${verticesInSatellite}`);
            }
        }
        progress(`Success, Satellite Vertex Collection document counts match`);
    };

    const testSatToSatEdgesExist = (collection) => {
        progress(`Testing, SatToSat Edge Collection document counts`);
        const shardList = collection.shards().sort();
        if (shardList.length !== 1) {
            throw new Error(`Satellite Collection "${collection.name()}" has more than 1 shard`);
        }
        const counts = collection.count(true);
        for (const shard of shardList) {
            if (counts[shard] !== verticesInSatellite) {
                throw new Error(`Mismatching counts on SatToSat Edge shard ${shard}, got ${counts[shard]} vs. ${verticesInSatellite}`);
            }
        }
        progress(`Success, SatToSat Edge Collection document counts match`);
    };

    const createGraphData = (isDisjoint, loopCount) => {
        const {
            satelliteCollectionName,
            verticesCollectionName,
            edgesCollectionName,
            edgesSatToSatCollectionName,
            edgesSatToSmartCollectionName,
            edgesSmartToSatCollectionName,
            smartGraphAttribute
        } =  generateNames(loopCount, isDisjoint);

        const shardKeys = generateSmartGraphShardKeys(db._collection(verticesCollectionName));
        createSmartVertices(db._collection(verticesCollectionName), shardKeys, smartGraphAttribute);
        createSatelliteVertices(db._collection(satelliteCollectionName));
        createSatToSatEdges(db._collection(edgesSatToSatCollectionName), satelliteCollectionName, satelliteCollectionName);
    }

    return {
        isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
            if (enterprise) {
                sgm = require('@arangodb/smart-graph');
            }
            let current = semver.parse(semver.coerce(currentVersion));

            return semver.gte(current, "3.9.0") && cluster && !options.readOnly && enterprise;
        },
        makeData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
            if (!isCluster || !isEnterprise) {
                throw new Error("Trying to create data for hybrid smart graphs, this is only possible for enterprise clusters.");
            }
            for (const isDisjoint of [true, false]) {
                createGraph(isDisjoint, loopCount)
                progress(`Created Hybrid ${isDisjoint ? "isDisjoint" : ""} Smart Graph`);
                createGraphData(isDisjoint, loopCount)
                progress('Created Data');
            }
        },
        checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
            if (!isCluster || !isEnterprise) {
                throw new Error("Trying to create data for hybrid smart graphs, this is only possible for enterprise clusters.");
            }
            for (const isDisjoint of [true, false]) {
                const {
                    smartGraphName,
                    satelliteCollectionName,
                    verticesCollectionName,
                    edgesCollectionName,
                    edgesSatToSatCollectionName,
                    edgesSatToSmartCollectionName,
                    edgesSmartToSatCollectionName,
                    smartGraphAttribute
                } = generateNames(loopCount, isDisjoint);
                testSmartVerticesExist(db._collection(verticesCollectionName));
                testSatelliteVerticesExist(db._collection(satelliteCollectionName));
                testSatToSatEdgesExist(db._collection(edgesSatToSatCollectionName));
            }

        },
        clearData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
            if (!isCluster || !isEnterprise) {
                throw new Error("Trying to create data for hybrid smart graphs, this is only possible for enterprise clusters.");
            }
            // Drop graph:
            let gsm = require("@arangodb/smart-graph");
            for (const isDisjoint of [true, false]) {
                const {
                    smartGraphName
                } =  generateNames(loopCount, isDisjoint);
                progress();

                try {
                    gsm._drop(smartGraphName, true);
                } catch (e) {
                }
            }
        }
    };
}());
