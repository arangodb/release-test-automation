#!/usr/bin/env python
""" Run a javascript command by spawning an arangosh
    to the configured connection """

from arangodb.async_client import ArangoCLIprogressiveTimeoutExecutor, default_line_result, make_default_params


class ArangoRestoreExecutor(ArangoCLIprogressiveTimeoutExecutor):
    """configuration"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes disable=too-many-statements disable=too-many-branches disable=too-many-locals
    def run_restore_monitored(
            self,
            basepath,
            args, progressive_timeout,
            verbose=True,
            result_line_handler=default_line_result,
            expect_to_fail=False):
        """
        runs an import in background tracing with
        a dynamic timeout that its got output
        (is still alive...)
        """
        run_cmd = (
            self.cfg.default_restore_args
            + [
                "--input-directory",
                str(basepath),
            ]
            + args
        )

        return self.run_arango_tool_monitored(
            self.cfg.bin_dir / "arangorestore",
            more_args=run_cmd,
            params=make_default_params(verbose, "restoring"),
            progressive_timeout=progressive_timeout,
            result_line_handler=result_line_handler,
            expect_to_fail=expect_to_fail,
        )
