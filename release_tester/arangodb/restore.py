#!/usr/bin/env python
""" Run a javascript command by spawning an arangosh
    to the configured connection """

from arangodb.async_client import ArangoCLIprogressiveTimeoutExecutor, dummy_line_result


class ArangoRestoreExecutor(ArangoCLIprogressiveTimeoutExecutor):
    """configuration"""

    # pylint: disable=dangerous-default-value

    def run_restore_monitored(self, basepath, args, timeout, verbose=True, expect_to_fail=False):
        # pylint: disable=too-many-arguments disable=too-many-instance-attributes disable=too-many-statements disable=too-many-branches disable=too-many-locals
        """
        runs an import in background tracing with
        a dynamic timeout that its got output
        (is still alive...)
        """
        run_cmd = self.cfg.default_restore_args + [
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
