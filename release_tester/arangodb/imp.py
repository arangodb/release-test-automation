#!/usr/bin/env python
""" Run a javascript command by spawning an arangosh
    to the configured connection """

from arangodb.async_client import (
    ArangoCLIprogressiveTimeoutExecutor,
    dummy_line_result
    )

def get_type_args(filename):
    """ guess the format by the filename """
    if filename.endswith('jsonl'):
        return ['--type=jsonl']
    if filename.endswith('json'):
        return ['--type=json']
    if filename.endswith('csv'):
        return ['--type=csv']
    raise NotImplementedError("no filename type encoding implemented for " + filename)

class ArangoImportExecutor(ArangoCLIprogressiveTimeoutExecutor):
    """ configuration """
    # pylint: disable=W0102

    def run_import_monitored(self, args, timeout, verbose=True):
       # pylint: disable=R0913 disable=R0902 disable=R0915 disable=R0912 disable=R0914
        """
        runs an import in background tracing with
        a dynamic timeout that its got output
        (is still alive...)
        """
        run_cmd = [
            "--log.level", "debug",
        ] + args

        return self.run_monitored(self.cfg.bin_dir / "arangoimport",
                                  run_cmd,
                                  timeout,
                                  dummy_line_result,
                                  verbose)

    def import_collection(self, collection_name, filename, more_args=[]):
        """ import into any collection """
        args = [
            '--collection', collection_name,
            '--file', filename
        ] + get_type_args(filename) + more_args

        ret = self.run_import_monitored(args,
                                        timeout=20,
                                        verbose=self.cfg.verbose)
        return ret

    def import_smart_edge_collection(self, collection_name, filename, edge_relations, more_args=[]):
        """ import into smart edge collection """
        if len(edge_relations) == 1:
            edge_relations[1] = edge_relations[0]
        args = [
            '--from-collection-prefix', edge_relations[0],
            '--to-collection-prefix', edge_relations[1]
        ] + more_args

        ret = self.import_collection(collection_name,
                                     filename,
                                     more_args=args)
        return ret
