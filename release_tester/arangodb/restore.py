#!/usr/bin/env python
""" Run a javascript command by spawning an arangosh
    to the configured connection """

from arangodb.async_client import ArangoCLIprogressiveTimeoutExecutor, dummy_line_result


class ArangoRestoreExecutor(ArangoCLIprogressiveTimeoutExecutor):
    """configuration"""

    # pylint: disable=W0102

    def run_restore_monitored(self, basepath, args, timeout, verbose=True, expect_to_fail=False):
        # pylint: disable=R0913 disable=R0902 disable=R0915 disable=R0912 disable=R0914
        """
        runs an import in background tracing with
        a dynamic timeout that its got output
        (is still alive...)
        """
        run_cmd = cfg.default_restore_args + [
            "--input-directory",
            str(basepath),
        ] + args

        return self.run_arango_tool_monitored(
            self.cfg.bin_dir / "arangorestore",
            run_cmd,
            timeout,
            dummy_line_result,
            verbose,
            expect_to_fail,
        )
