#!/usr/bin/env python
""" Run a javascript command by spawning an arangosh
    to the configured connection """

from arangodb.async_client import ArangoCLIprogressiveTimeoutExecutor, dummy_line_result


def get_type_args(filename):
    """guess the format by the filename"""
    if str(filename).endswith("jsonl"):
        return ["--type=jsonl"]
    if str(filename).endswith("json"):
        return ["--type=json"]
    if str(filename).endswith("csv"):
        return ["--type=csv"]
    raise NotImplementedError("no filename type encoding implemented for " + filename)


class ArangoImportExecutor(ArangoCLIprogressiveTimeoutExecutor):
    """configuration"""

    # pylint: disable=dangerous-default-value

    def run_import_monitored(self, args, timeout, verbose=True, expect_to_fail=False):
        # pylint: disable=too-many-arguments disable=too-many-instance-attributes disable=too-many-statements disable=too-many-branches disable=too-many-locals
        """
        runs an import in background tracing with
        a dynamic timeout that its got output
        (is still alive...)
        """
        run_cmd = self.cfg.default_imp_args + [
            "--log.level",
            "debug",
        ] + args

        return self.run_arango_tool_monitored(
            self.cfg.bin_dir / "arangoimport",
            run_cmd,
            timeout,
            dummy_line_result,
            verbose,
            expect_to_fail,
        )

    def import_collection(self, collection_name, filename, more_args=[]):
        """import into any collection"""
        # fmt: off
        args = [
            '--collection', collection_name,
            '--file', filename
        ] + get_type_args(filename) + more_args
        # fmt: on

        ret = self.run_import_monitored(args, timeout=20, verbose=self.cfg.verbose)
        return ret

    def import_smart_edge_collection(self, collection_name, filename, edge_relations, more_args=[]):
        """import into smart edge collection"""
        if len(edge_relations) == 1:
            edge_relations.append(edge_relations[0])
        # fmt: off
        args = [
            '--from-collection-prefix', edge_relations[0],
            '--to-collection-prefix', edge_relations[1]
        ] + more_args
        # fmt: on

        ret = self.import_collection(collection_name, filename, more_args=args)
        return ret
