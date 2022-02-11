/* global fs, PWD, writeGraphData, getShardCount, getReplicationFactor,  print, progress, db, createSafe, _, semver */

(function () {
    const Joi = require('joi');
    const {arango} = require('@arangodb');
    const chai = require('chai');
    const expect = chai.expect;

    const diffHelper = (actual, expected) => {
        if (Array.isArray(actual) && Array.isArray(expected)) {
            if (actual.length !== expected.length) {
                return `${actual} !== ${expected}`;
            }
            const result = [];
            for (let i = 0; i < actual.length; ++i) {
                const res = diffHelper(actual[i], expected[i]);
                if (res !== true) {
                    result.push({entry: i, message: res});
                }
            }
            if (result.length === 0) {
                return true;
            }
            return result;
        }
        if (actual instanceof Object && expected instanceof Object) {
            const expectedKeys = Object.keys(expected);
            const result = [];

            for (const k of _.difference(Object.keys(actual), expectedKeys)) {
                result.push({key: k, message: "Is added, but not expected"});
            }
            for (const k of expectedKeys) {
                const res = diffHelper(actual[k], expected[k]);
                if (res !== true) {
                    result.push({key: k, message: res});
                }
            }
            if (result.length === 0) {
                return true;
            }
            return result;
        }
        if (actual === expected) {
            return true;
        } else {
            return `${actual} !== ${expected}`;
        }
    }

    let sgm;
    const numberOfShards = 7;
    const verticesInSatellite = 13;
    const localStorageName = "UnitTestHybridSmartGraph_local_storage";

    const createStorage = () => {
        const col = createSafe(localStorageName, name => db._create(name), name => db._collection(name));
        const store = (_key, data) => {
            col.save({_key, data});
        };
        return {store};
    };
    const loadStorage = () => {
        const col = db._collection(localStorageName);
        if (!col) {
            throw new Error(`Local Storage ${localStorage} is not available anymore.`);
        }
        const read = (key) => {
            const doc = col.document(key);
            if (!doc) {
                throw new Error(`Expected key ${key} not found Local Storage ${localStorage}.`);
            }
            return doc.data
        };
        return {read};
    }
    const clearStorage = () => {
        try {
            db._drop(localStorageName);
        } catch (e) {
        }
    };

    const url = '/_api/gharial';
    const generateSingleUrlWithDetails = (graphName) => {
        return `${url}/${graphName}?details=true`;
    };
    // basic validation methods
    const validateBasicGraphResponse = (res) => {
        expect(res.code).to.equal(200);
        expect(res.error).to.be.false;
        expect(res).to.have.keys("error", "code", "graph");
        expect(res.graph).to.be.an('object');
    };

    const applyGraphIgnoreList = (props) => {
        const ignoreList = [];
        return _.omit(props, ignoreList);
    };
    const applyCollectionIgnoreList = (props) => {
        const ignoreList = [];
        return _.omit(props, []);
    };


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

    const createGraph = (isDisjoint, loopCount, store) => {
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
        const g = createSafe(smartGraphName, graphName => {
            require("console").warn(options);
            const g = sgm._create(graphName, edgeDefinitions, [], options);
            require("console").warn(`On create: ${JSON.stringify(db._collection(satelliteCollectionName).properties(true))}`);
            return g

        }, graphName => {
            return sgm._graph(graphName);
        });
        const res = arango.GET(generateSingleUrlWithDetails(smartGraphName));
        validateBasicGraphResponse(res);
        validateGraphFormat(res.graph, {
            isSmart: true,
            isDisjoint,
            hasDetails,
            hybridCollections: [satelliteCollectionName]
        });
        // Persist all relevant properties
        store(`gharial_${smartGraphName}`, applyGraphIgnoreList(res.graph));
        for (const cname of [
            satelliteCollectionName,
            verticesCollectionName,
            edgesCollectionName,
            edgesSatToSatCollectionName,
            edgesSatToSmartCollectionName,
            edgesSmartToSatCollectionName
        ]) {
            store(`props_${cname}`, applyCollectionIgnoreList(db._collection(cname).properties(true)));
        }
        return g;
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
    const expectedNumberOfDocuments = (shardKeys) => {
        return shardKeys.map((_, index) => (index + 1) * 2);
    };


    /// @brief, helper method to create Smart-sharded documents.
    /// Will create expectedNumberOfDocuments vertices in every respective shard.
    const createSmartVertices = (collection, shardKeys, smartGraphAttribute) => {
        const numDocs = expectedNumberOfDocuments(shardKeys);
        const docs = [];
        for (let i = 0; i < shardKeys.length; ++i) {
            const shardKey = shardKeys[i];
            // Insert expected NumberOfDocuments many documents into each different shardkey.
            for (let c = 0; c < numDocs[i]; ++c) {
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

    /// @brief, helper method to create satellite->satellite edges.
    /// Will create verticesInSatellite many edges inside the Satellite->Satellite collection
    const createSatToSmartEdges = (collection, fromCol, toCol, isDisjoint, shardKeys) => {
        const shardList = collection.shards().sort();
        const docs = [];
        if (!isDisjoint) {
            if (shardList.length !== 1) {
                throw new Error(`Non-Disjoint SatToSmart Edge Collection "${collection.name()}" has more than 1 shard`);
            }
        }
        const numDocs = expectedNumberOfDocuments(shardKeys);
        for (let i = 0; i < shardKeys.length; ++i) {
            const shardKey = shardKeys[i];
            // Insert expected NumberOfDocuments many documents into each different shardkey.
            for (let c = 0; c < numDocs[i]; ++c) {
                docs.push({_from: `${fromCol}/abc`, _to: `${toCol}/${shardKey}:abc`});
            }
        }
        collection.save(docs);
        progress(`Created SatToSmart Edges`);
    };

    /// @brief, helper method to create satellite->satellite edges.
    /// Will create verticesInSatellite many edges inside the Satellite->Satellite collection
    const createSmartToSatEdges = (collection, fromCol, toCol, isDisjoint, shardKeys) => {
        const shardList = collection.shards().sort();
        if (!isDisjoint) {
            if (shardList.length !== 1) {
                throw new Error(`Non-Disjoint SmartToSat Edge Collection "${collection.name()}" has more than 1 shard`);
            }
        }
        const numDocs = expectedNumberOfDocuments(shardKeys);
        const docs = [];
        for (let i = 0; i < shardKeys.length; ++i) {
            const shardKey = shardKeys[i];
            // Insert expected NumberOfDocuments many documents into each different shardkey.
            for (let c = 0; c < numDocs[i]; ++c) {
                docs.push({_from: `${fromCol}/${shardKey}:abc`, _to: `${toCol}/abc`});
            }
        }
        collection.save(docs);
        progress(`Created SmartToSat Edges`);
    };

    /// @brief, helper method to create smart->smart edges.
    /// Will create verticesInSatellite many edges inside the Satellite->Satellite collection
    const createSmartToSmartEdges = (collection, fromCol, toCol, isDisjoint, shardKeys) => {
        const shardList = collection.shards().sort();
        const docs = [];
        if (isDisjoint) {
            const numDocs = expectedNumberOfDocuments(shardKeys);
            for (let i = 0; i < shardKeys.length; ++i) {
                const shardKey = shardKeys[i];
                // Insert expected NumberOfDocuments many documents into each different shardkey.
                for (let c = 0; c < numDocs[i]; ++c) {
                    docs.push({_from: `${fromCol}/${shardKey}:abc`, _to: `${toCol}/${shardKey}:abc`});
                }
            }
        } else {
            const numDocs = expectedNumberOfDocuments(shardKeys);
            // The following mechanism has the follow properties:
            // a) Every _local_ and _from_ shard will have a different count()
            // b) _from_ and _to_ shards are symmetric, the first shard of _from_
            // has the same count as the first shard of _to_.
            for (let i = 0; i < shardKeys.length; ++i) {
                const fromShardKey = shardKeys[i];
                for (let j = 0; j < shardKeys.length; ++j) {
                    const toShardKey = shardKeys[j];
                    if (i === j) {
                        // Insert expected NumberOfDocuments many documents for _local_edges
                        for (let c = 0; c < numDocs[i]; ++c) {
                            docs.push({_from: `${fromCol}/${fromShardKey}:abc`, _to: `${toCol}/${toShardKey}:abc`});
                        }
                    } else {
                        // Insert expected NumberOfDocuments many documents based on the _from_ and the same based on the _to_ shardKey
                        for (let c = 0; c < numDocs[i] + numDocs[j]; ++c) {
                            docs.push({_from: `${fromCol}/${fromShardKey}:abc`, _to: `${toCol}/${toShardKey}:abc`});
                        }
                    }
                }

            }
        }

        collection.save(docs);
        progress(`Created SmartToSmart Edges ${docs.length}`);
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
        } = generateNames(loopCount, isDisjoint);

        const shardKeys = generateSmartGraphShardKeys(db._collection(verticesCollectionName));
        createSmartVertices(db._collection(verticesCollectionName), shardKeys, smartGraphAttribute);
        createSatelliteVertices(db._collection(satelliteCollectionName));
        createSatToSatEdges(db._collection(edgesSatToSatCollectionName), satelliteCollectionName, satelliteCollectionName);
        createSatToSmartEdges(db._collection(edgesSatToSmartCollectionName), satelliteCollectionName, verticesCollectionName, isDisjoint, shardKeys);
        createSmartToSatEdges(db._collection(edgesSmartToSatCollectionName), verticesCollectionName, satelliteCollectionName, isDisjoint, shardKeys);
        createSmartToSmartEdges(db._collection(edgesCollectionName), verticesCollectionName, verticesCollectionName, isDisjoint, shardKeys);
    };

    /***************
     * Section for existence tests
     ***************/

        // @brief validates the graph format including all expected properties.
        // Expected values depends on the environment.
    const validateGraphFormat = (
            graph,
            validationProperties
        ) => {
            const isSmart = (validationProperties && validationProperties.isSmart) || false;
            const isDisjoint = (validationProperties && validationProperties.isDisjoint) || false;
            const isSatellite = (validationProperties && validationProperties.isSatellite) || false;
            const hasDetails = (validationProperties && validationProperties.hasDetails) || false;
            const hybridCollections = (validationProperties && validationProperties.hybridCollections) || [];
            const onlySatellitesCreated = (validationProperties && validationProperties.onlySatellitesCreated) || false;
            /*
             * Edge Definition Schema
             */
            let edgeDefinitionSchema;
            if (hasDetails) {
                edgeDefinitionSchema = Joi.object({
                    collection: Joi.string().required(),
                    from: Joi.array().items(Joi.string()).required(),
                    to: Joi.array().items(Joi.string()).required(),
                    checksum: Joi.number().unsafe().required()
                });
            } else {
                edgeDefinitionSchema = Joi.object({
                    collection: Joi.string().required(),
                    from: Joi.array().items(Joi.string()).required(),
                    to: Joi.array().items(Joi.string()).required()
                });
            }
            Object.freeze(edgeDefinitionSchema);

            /*
             * Collection Properties Schema
             */

            // This is always required to be available
            let generalGraphSchema = {
                "_key": Joi.string().required(),
                "_rev": Joi.string().required(),
                "_id": Joi.string().required(),
                name: Joi.string().required(),
                orphanCollections: Joi.array().items(Joi.string()).required(),
                edgeDefinitions: Joi.array().items(edgeDefinitionSchema).required()
            };
            if (hasDetails) {
                generalGraphSchema.checksum = Joi.number().unsafe().required();
            }

            if (isCluster || isSmart || isSatellite) {
                // Those properties are either:
                // - Required for all graphs which are being created in a cluster
                // - OR SmartGraphs (incl. Disjoint & Hybrid, as SmartGraphs can now be created
                //   in a SingleServer environment as well)
                const distributionGraphSchema = {
                    numberOfShards: Joi.number().integer().min(1).required(),
                    isSmart: Joi.boolean().required(),
                    isSatellite: Joi.boolean().required()
                };

                if (isSatellite) {
                    distributionGraphSchema.replicationFactor = Joi.string().valid('satellite').required();
                } else {
                    distributionGraphSchema.replicationFactor = Joi.number().integer().min(1).required();
                    distributionGraphSchema.minReplicationFactor = Joi.number().integer().min(1).required();
                    distributionGraphSchema.writeConcern = Joi.number().integer().min(1).required();
                }

                Object.assign(generalGraphSchema, distributionGraphSchema);
            }

            if (isSmart) {
                // SmartGraph related only
                let smartGraphSchema = {
                    smartGraphAttribute: Joi.string().required(),
                    isDisjoint: Joi.boolean().required()
                };
                if (isDisjoint) {
                    expect(graph.isDisjoint).to.be.true;
                }
                Object.freeze(smartGraphSchema);
                Object.assign(generalGraphSchema, smartGraphSchema);
            }

            if ((isSmart || isSatellite) && !onlySatellitesCreated) {
                let smartOrSatSchema = {
                    initial: Joi.string().required(),
                    initialCid: Joi.number().integer().min(1).required()
                };
                Object.freeze(smartOrSatSchema);
                Object.assign(generalGraphSchema, smartOrSatSchema);
            }

            if (hasDetails && isSmart && !isSatellite) {
                // This is a special case, means:
                // Combination out of a SmartGraph and additional collections which
                // should be created as SatelliteCollections. In that case the API
                // should expose the collections which are created as satellites as
                // well. Otherwise, it will be an empty array.
                const hybridSmartGraphSchema = {
                    satellites: Joi.array().items(Joi.string()).required()
                };

                Object.assign(generalGraphSchema, hybridSmartGraphSchema);

                if (hybridCollections.length > 0) {
                    require("console").warn(JSON.stringify(graph));
                    require("console").warn(JSON.stringify(hybridCollections));

                    hybridCollections.forEach((hybridCol) => {
                        require("console").warn(JSON.stringify(db._collection(hybridCol).properties(true)));
                        expect(graph.satellites.indexOf(hybridCol)).to.be.greaterThan(-1);
                    });
                } else {
                    expect(graph.satellites).to.be.an('array');
                    expect(graph.satellites.length).to.equal(0);
                }
            }

            // now create the actual joi object out of the completed schema combination
            generalGraphSchema = Joi.object(generalGraphSchema);

            // start schema validation
            const res = generalGraphSchema.validate(graph);
            expect(res.error).to.be.null;
        };


    const testSmartVerticesExist = (collection) => {
        progress(`Testing, Smart Vertex Collection document counts`);
        const shardList = collection.shards().sort();
        const numDocs = expectedNumberOfDocuments(shardList);
        const counts = collection.count(true);
        for (let i = 0; i < shardList.length; ++i) {
            if (counts[shardList[i]] !== numDocs[i]) {
                throw new Error(`Mismatching counts on Smart Vertex shard ${shardList[i]}, got ${counts[shardList[i]]} vs. ${numDocs[i]}`);
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
        for (let i = 0; i < shardList.length; ++i) {
            if (counts[shardList[i]] !== verticesInSatellite) {
                throw new Error(`Mismatching counts on Satellite Vertex shard ${shardList[i]}, got ${counts[shardList[i]]} vs. ${verticesInSatellite}`);
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
        for (let i = 0; i < shardList.length; ++i) {
            if (counts[shardList[i]] !== verticesInSatellite) {
                throw new Error(`Mismatching counts on SatToSat Edge shard ${shardList[i]}, got ${counts[shardList[i]]} vs. ${verticesInSatellite}`);
            }
        }
        progress(`Success, SatToSat Edge Collection document counts match`);
    };

    const testSatToSmartEdgesExist = (collection, isDisjoint, shardKeys) => {
        progress(`Testing, SatToSmart Edge Collection document counts`);
        const numDocs = expectedNumberOfDocuments(shardKeys);
        const shardList = collection.shards().sort();
        if (isDisjoint) {

        } else {
            if (shardList.length !== 1) {
                throw new Error(`In non-disjoint case SmartToSat Collection "${collection.name()}" has more than 1 shard`);
            }
        }
        const counts = collection.count(true);
        for (let i = 0; i < shardList.length; ++i) {
            if (counts[shardList[i]] !== verticesInSatellite) {
                throw new Error(`Mismatching counts on SatToSat Edge shard ${shardList[i]}, got ${counts[shardList[i]]} vs. ${verticesInSatellite}`);
            }
        }
        progress(`Success, SatToSat Edge Collection document counts match`);
    };

    const testGraphDefinitionAndCollections = (isDisjoint, loopCount, read) => {
        const {
            smartGraphName,
            verticesCollectionName,
            satelliteCollectionName,
            edgesCollectionName,
            edgesSatToSatCollectionName,
            edgesSatToSmartCollectionName,
            edgesSmartToSatCollectionName
        } = generateNames(loopCount, isDisjoint);

        const res = arango.GET(generateSingleUrlWithDetails(smartGraphName));
        validateBasicGraphResponse(res);

        validateGraphFormat(res.graph, {
            isSmart: true,
            isDisjoint,
            hasDetails,
            hybridCollections: [satelliteCollectionName]
        });

        // Make sure response is identical
        const expectedGraph = read(`gharial_${smartGraphName}`);
        const actual = applyCollectionIgnoreList(res.graph);
        expect(actual).to.deep.equal(expectedGraph, `${JSON.stringify(diffHelper(actual, expectedGraph))}`);

        // Test Collection properties:
        for (const cname of [
            satelliteCollectionName,
            verticesCollectionName,
            edgesCollectionName,
            edgesSatToSatCollectionName,
            edgesSatToSmartCollectionName,
            edgesSmartToSatCollectionName
        ]) {
            const expected = read(`props_${cname}`);
            const actual = applyCollectionIgnoreList(db._collection(cname).properties(true));
            expect(actual).to.deep.equal(expected, `${JSON.stringify(diffHelper(actual, expected))}`);
        }
    };

    const testGraphData = (isDisjoint, loopCount) => {
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
    };

    let hasDetails = true;
    return {
        isSupported: function (currentVersion, oldVersion, options, enterprise, cluster) {
            if (enterprise) {
                sgm = require('@arangodb/smart-graph');
            }
            let current = semver.parse(semver.coerce(currentVersion));
            //hasDetails = semver.gte(current, "3.9.1");

            return semver.gte(current, "3.9.0") && cluster && !options.readOnly && enterprise;
        },
        makeData: function (options, isCluster, isEnterprise, dbCount, loopCount) {
            if (!isCluster || !isEnterprise) {
                throw new Error("Trying to create data for hybrid smart graphs, this is only possible for enterprise clusters.");
            }
            const {store} = createStorage();
            for (const isDisjoint of [true, false]) {
                const disjointPrefix = isDisjoint ? "isDisjoint" : "";
                createGraph(isDisjoint, loopCount, store)
                progress(`Creating Hybrid ${disjointPrefix} Smart Graph`);
                createGraphData(isDisjoint, loopCount)
                progress(`Success Created Hybrid ${disjointPrefix} Smart Graph Data`);

            }
        },
        checkData: function (options, isCluster, isEnterprise, dbCount, loopCount, readOnly) {
            if (!isCluster || !isEnterprise) {
                throw new Error("Trying to create data for hybrid smart graphs, this is only possible for enterprise clusters.");
            }
            try {
                const {read} = loadStorage();
                for (const isDisjoint of [true, false]) {
                    progress(`Testing Hybrid ${isDisjoint ? "isDisjoint" : ""} Smart Graph`);
                    testGraphDefinitionAndCollections(isDisjoint, loopCount, read);
                    testGraphData(isDisjoint, loopCount)
                    progress(`Success Testing Hybrid ${isDisjoint ? "isDisjoint" : ""} Smart Graph Data`);
                }
            } catch (e) {
                e.stack.split("\n").map(frame => require("console").error(frame));
                throw e;
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
                } = generateNames(loopCount, isDisjoint);
                progress();

                try {
                    gsm._drop(smartGraphName, true);
                } catch (e) {
                }
            }
            clearStorage();
        }
    };
}());
