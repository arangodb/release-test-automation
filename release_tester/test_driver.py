# pylint: disable=R0913 disable=R0914, disable=W0703, disable=R0912, disable=R0915
def run_upgrade(
    versions: list,
    verbose,
    package_dir,
    test_data_dir,
    alluredir,
    clean_alluredir,
    zip_package,
    hot_backup,
    interactive,
    starter_mode,
    stress_upgrade,
    abort_on_error,
    publicip,
    selenium,
    selenium_driver_args,
    use_auto_certs,
    run_props: RunProperties
):
    """execute upgrade tests"""
    lh.section("startup")
    results = []
    for runner_type in STARTER_MODES[starter_mode]:
        installers = create_config_installer_set(
            versions,
            verbose,
            zip_package,
            hot_backup,
            Path(package_dir),
            Path(test_data_dir),
            "all",
            publicip,
            interactive,
            stress_upgrade,
            run_props,
        )
        old_inst = installers[0][1]
        new_inst = installers[1][1]

        with AllureTestSuiteContext(
            alluredir,
            clean_alluredir,
            run_props,
            zip_package,
            versions,
            None,
            True,
            runner_strings[runner_type],
            None,
            new_inst.installer_type,
        ):
            with RtaTestcase(runner_strings[runner_type] + " main flow") as testcase:
                if (not run_props.enterprise or is_windows) and runner_type == RunnerType.DC2DC:
                    testcase.context.status = Status.SKIPPED
                    testcase.context.statusDetails = StatusDetails(
                        message="DC2DC is not applicable to Community packages."
                    )
                    continue
                one_result = {
                    "testrun name": run_props.testrun_name,
                    "testscenario": runner_strings[runner_type],
                    "success": True,
                    "messages": [],
                    "progress": "",
                }
                try:
                    kill_all_processes()
                    runner = None
                    lh.section("configuration")
                    print(
                        """
                    starter mode: {starter_mode}
                    old version: {old_version}
                    {cfg_repr}
                    """.format(
                            **{
                                "starter_mode": str(starter_mode),
                                "old_version": str(versions[0]),
                                "cfg_repr": repr(installers[1][0]),
                            }
                        )
                    )
                    if runner_type:
                        runner = make_runner(
                            runner_type,
                            abort_on_error,
                            selenium,
                            selenium_driver_args,
                            installers,
                            run_props,
                            use_auto_certs=use_auto_certs,
                        )
                        if runner:
                            try:
                                runner.run()
                                runner.cleanup()
                                testcase.context.status = Status.PASSED
                            except Exception as ex:
                                one_result["success"] = False
                                one_result["messages"].append(str(ex))
                                one_result["progress"] += runner.get_progress()
                                runner.take_screenshot()
                                runner.agency_acquire_dump()
                                runner.search_for_warnings()
                                runner.quit_selenium()
                                kill_all_processes()
                                runner.zip_test_dir()
                                testcase.context.status = Status.FAILED
                                testcase.context.statusDetails = StatusDetails(
                                    message=str(ex),
                                    trace="".join(traceback.TracebackException.from_exception(ex).format()),
                                )
                                if abort_on_error:
                                    raise ex
                                traceback.print_exc()
                                lh.section("uninstall on error")
                                old_inst.un_install_debug_package()
                                old_inst.un_install_server_package()
                                old_inst.cleanup_system()
                                try:
                                    runner.cleanup()
                                finally:
                                    pass
                                continue
                            if runner.ui_tests_failed:
                                failed_test_names = [
                                    f'"{row["Name"]}"'
                                    for row in runner.ui_test_results_table
                                    if not row["Result"] == "PASSED"
                                ]
                                one_result["success"] = False
                                one_result["messages"].append(
f'The following UI tests failed: {", ".join(failed_test_names)}. See allure report for details.'
                                )
                    lh.section("uninstall")
                    new_inst.un_install_server_package()
                    lh.section("check system")
                    new_inst.check_uninstall_cleanup()
                    lh.section("remove residuals")
                    try:
                        old_inst.cleanup_system()
                    except Exception:
                        print("Ignoring old cleanup error!")
                    try:
                        print("Ignoring new cleanup error!")
                        new_inst.cleanup_system()
                    except Exception:
                        print("Ignoring general cleanup error!")
                except Exception as ex:
                    print("Caught. " + str(ex))
                    one_result["success"] = False
                    one_result["messages"].append(str(ex))
                    one_result["progress"] += "\naborted outside of testcodes"
                    if abort_on_error:
                        print("re-throwing.")
                        raise ex
                    traceback.print_exc()
                    kill_all_processes()
                    if runner:
                        try:
                            runner.cleanup()
                        except Exception as exception:
                            print("Ignoring runner cleanup error! Exception:")
                            print(str(exception))
                            print("".join(traceback.TracebackException.from_exception(exception).format()))
                    try:
                        print("Cleaning up system after error:")
                        old_inst.un_install_debug_package()
                        old_inst.un_install_server_package()
                        old_inst.cleanup_system()
                    except Exception:
                        print("Ignoring old cleanup error!")
                    try:
                        print("Ignoring new cleanup error!")
                        new_inst.un_install_debug_package()
                        new_inst.un_install_server_package()
                        new_inst.cleanup_system()
                    except Exception:
                        print("Ignoring new cleanup error!")
                results.append(one_result)
    return results

# fmt: off
# pylint: disable=R0913 disable=R0914
def run_test(mode,
             versions: list,
             verbose,
             package_dir,
             test_data_dir,
             alluredir,
             clean_alluredir,
             zip_package,
             hot_backup,
             interactive,
             starter_mode,
             abort_on_error,
             publicip,
             selenium,
             selenium_driver_args,
             use_auto_certs,
             run_props: RunProperties
):
# fmt: on
    """ main """
    lh.configure_logging(verbose)
    results = []

    do_install = mode in ["all", "install"]
    do_uninstall = mode in ["all", "uninstall"]

    installers = create_config_installer_set(
        versions,
        verbose,
        zip_package,
        hot_backup,
        Path(package_dir),
        Path(test_data_dir),
        mode,
        publicip,
        interactive,
        False,
        run_props
    )
    lh.section("configuration")
    print(
        """
    mode: {mode}
    {cfg_repr}
    """.format(
            **{"mode": str(mode), "cfg_repr": repr(installers[0][0])}
        )
    )

    count = 1
    for runner_type in STARTER_MODES[starter_mode]:
        with AllureTestSuiteContext(alluredir,
                                    clean_alluredir,
                                    run_props,
                                    zip_package,
                                    versions,
                                    True,
                                    None,
                                    runner_strings[runner_type],
                                    None,
                                    installers[0][1].installer_type):
            with RtaTestcase(runner_strings[runner_type] + " main flow") as testcase:
                if (runner_type == RunnerType.DC2DC and
                    (not run_props.enterprise or WINVER[0] != "")):
                    testcase.context.status = Status.SKIPPED
                    testcase.context.statusDetails = StatusDetails(
                        message="DC2DC is not applicable to Community packages.")
                    continue
                runner = make_runner(
                    runner_type,
                    abort_on_error,
                    selenium,
                    selenium_driver_args,
                    installers,
                    run_props,
                    use_auto_certs=use_auto_certs,
                )
                # install on first run:
                runner.do_install = (count == 1) and do_install
                # only uninstall after the last test:
                runner.do_uninstall = (count == len(STARTER_MODES[starter_mode])) and do_uninstall
                one_result = {
                    "testrun name": run_props.testrun_name,
                    "testscenario": runner_strings[runner_type],
                    "success": True,
                    "messages": [],
                    "progress": "",
                }
                try:
                    runner.run()
                    runner.cleanup()
                    testcase.context.status = Status.PASSED
                # pylint: disable=W0703
                except Exception as ex:
                    one_result["success"] = False
                    one_result["messages"].append(str(ex))
                    one_result["progress"] += runner.get_progress()
                    runner.take_screenshot()
                    runner.agency_acquire_dump()
                    runner.search_for_warnings()
                    runner.quit_selenium()
                    kill_all_processes()
                    runner.zip_test_dir()
                    testcase.context.status = Status.FAILED
                    testcase.context.statusDetails = StatusDetails(message=str(ex),
                                                                   trace="".join(
                                                                       traceback.TracebackException.from_exception(
                                                                           ex).format()))
                    if abort_on_error:
                        raise ex
                    traceback.print_exc()
                    lh.section("uninstall on error")
                    try:
                        runner.cleanup()
                    finally:
                        pass
                    continue

                if runner.ui_tests_failed:
                    failed_test_names = [f'"{row["Name"]}"' for row in
                                         runner.ui_test_results_table if
                                         not row["Result"] == "PASSED"]
                    one_result["success"] = False
                    one_result[
                        "messages"].append(
f'The following UI tests failed: {", ".join(failed_test_names)}. See allure report for details.')

                kill_all_processes()
                count += 1

    return results
