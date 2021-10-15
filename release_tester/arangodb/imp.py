#!/usr/bin/env python
""" Run a javascript command by spawning an arangosh
    to the configured connection """

import json
import csv
import ctypes

from arangodb.async_client import ArangoCLIprogressiveTimeoutExecutor, dummy_line_result


def get_type_args(filename):
    """guess the format by the filename"""
    if filename.endswith("jsonl"):
        return ["--type=jsonl"]
    if filename.endswith("json"):
        return ["--type=json"]
    if filename.endswith("csv"):
        return ["--type=csv"]
    if filename == "-":
        return ["--type=jsonl"]
    raise NotImplementedError("no filename type encoding implemented for " + filename)

month_decode = {
    "JAN":"01",
    "FEB":"02",
    "MAR":"03",
    "APR":"04",
    "MAY":"05",
    "JUN":"06",
    "JUL":"07",
    "AUG":"08",
    "SEP":"09",
    "OCT":"10",
    "NOV":"11",
    "DEC":"12"
}

def decode_date(date):
    """convert date to something more arango'ish"""
    if len(date) == 24:
        month = date[3:6]
        day = date[0:2]
        year = date[7:11]
        time = date[12:24]
        year += "-"
        year += month_decode.get(month, "01")
        year += "-"
        year += day
        year += "T"
        year += time
        return year
    return date

class ArangoImportExecutor(ArangoCLIprogressiveTimeoutExecutor):
    """configuration"""

    # pylint: disable=W0102
    def __init__(self, config, connect_instance):
        super().__init__(config, connect_instance)
        self.wikidata_reader = None
        self.wikidata_nlines = 0

    def run_import_monitored(self, args, timeout, verbose=True, expect_to_fail=False, writer=None):
        # pylint: disable=R0913 disable=R0902 disable=R0915 disable=R0912 disable=R0914
        """
        runs an import in background tracing with
        a dynamic timeout that its got output
        (is still alive...)
        """
        run_cmd = [
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
            writer=writer
        )

    def import_collection(self, collection_name, filename, more_args=[], writer=None):
        """import into any collection"""
        # fmt: off
        args = [
            '--collection', collection_name,
            '--file', filename
        ] + get_type_args(filename) + more_args
        # fmt: on

        ret = self.run_import_monitored(args, timeout=20, verbose=self.cfg.verbose, writer=writer)
        return ret

    def import_smart_edge_collection(self, collection_name, filename, edge_relations, more_args=[]):
        """import into smart edge collection"""
        if len(edge_relations) == 1:
            edge_relations[1] = edge_relations[0]
        # fmt: off
        args = [
            '--from-collection-prefix', edge_relations[0],
            '--to-collection-prefix', edge_relations[1]
        ] + more_args
        # fmt: on

        ret = self.import_collection(collection_name, filename, more_args=args)
        return ret

    def wikidata_writer(self):
        """pipe wikidata file into improter while translating it"""
        count = 0
        for row in self.wikidata_reader:
            count += 1
            if count > self.wikidata_nlines:
                print("imported enough, aborting.")
                break
            if count > 1: # headline, we don't care...
                line = json.dumps({
                    'title': row[0],
                    'body': row[2],
                    'count': count,
                    'created':decode_date(row[1])}) + "\n"
                print(line)
                self.process.stdin.write(line.encode())
        self.process.stdin.close()

    def import_wikidata(self, collection_name, nlines, filename, more_args=[]):
        """import by write piping"""
        filedes = filename.open("r", encoding='utf-8', errors='replace')
        self.wikidata_reader = csv.reader(filedes, delimiter='\t')
        self.wikidata_nlines = nlines
        # Override csv default 128k field size
        csv.field_size_limit(int(ctypes.c_ulong(-1).value // 2))

        # args = get_type_args('foo.json') + more_args
        args = ['--create-collection', 'true' ] + more_args
        ret = self.import_collection(
            collection_name,
            filename="-",
            more_args=args,
            writer=ArangoImportExecutor.wikidata_writer)
        return ret
