#!/usr/bin/env python3
""" views testsuite """

import semver
import traceback
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase
from selenium_ui_test.pages.views_page import ViewsPage
import time



class ViewsTestSuite(BaseSeleniumTestSuite):
    """ views testsuite """
    @testcase
    def test_views(self):
        """testing Views page"""
        # pylint: disable=too-many-statements
        self.tprint("---------Checking Views Begin--------- \n")
        views = ViewsPage(self.webdriver, self.cfg, self.video_start_time)  # creating obj for viewPage
        assert views.current_user() == "ROOT", "current user is root?"
        assert views.current_database() == "_SYSTEM", "current database is _system?"

        self.exception = False
        self.error = None

        try:
            self.tprint("Selecting Views tab\n")
            views.navbar_goto("views")

            # creating v3.9.x and v3.10.x for improved views
            if views.current_package_version() >= semver.VersionInfo.parse("3.9.0"):
                
                # creating v3.11.3 and v3.12.x improved view for the new UI
                if views.current_package_version() >= semver.VersionInfo.parse("3.11.0"):
                    views.create_improved_views_311(
                        "arangosearch_view_3111", "arangosearch", 0
                    )
                    views.create_improved_views_311(
                        "arangosearch_view_3112", "arangosearch", 0
                    )
                    # views.create_improved_views_311(
                    #         "search_alias", "search-alias", 0
                    #     )
                    self.tprint("Creating improved views completed \n")
                
                # Creating improved views for v3.9.x and v3.10.x
                if (
                    semver.VersionInfo.parse("3.9.100")
                    < views.current_package_version()
                    < semver.VersionInfo.parse("3.10.100")
                ):
                    views.create_improved_views("improved_arangosearch_view_01", 0)
                    views.create_improved_views("improved_arangosearch_view_02", 1)
                
                # Checking improved views for v3.10.x
                if semver.VersionInfo.parse("3.9.100") < views.current_package_version() < semver.VersionInfo.parse("3.10.100"):
                    views.checking_improved_views_for_v310(
                        "improved_arangosearch_view_01",
                        views.select_improved_arangosearch_view_01,
                        self.is_cluster
                    )
                
                # Checking improved views for v3.9.x
                if (
                    semver.VersionInfo.parse("3.8.100")
                    < views.current_package_version()
                    < semver.VersionInfo.parse("3.9.100")
                ):
                    views.checking_improved_views(
                        "improved_arangosearch_view_01",
                        views.select_improved_arangosearch_view_01,
                        self.is_cluster
                    )

            elif views.current_package_version() <= semver.VersionInfo.parse("3.8.100"):
                views.create_new_views('firstView')
                views.create_new_views('secondView')

                views.select_views_settings()
                self.tprint("Sorting views to descending\n")
                views.select_sorting_views()
                self.tprint("Sorting views to ascending\n")
                views.select_sorting_views()

                self.tprint("search views option testing\n")
                views.search_views("secondView", views.search_second_view)
                views.search_views("firstView", views.search_first_view)

                self.tprint("Selecting first Views \n")
                views.select_first_view()
                self.tprint("Selecting collapse button \n")
                views.select_collapse_btn()
                self.tprint("Selecting expand button \n")
                views.select_expand_btn()
                self.tprint("Selecting editor mode \n")
                views.select_editor_mode_btn(0)
                self.tprint("Switch editor mode to Code \n")
                views.switch_to_code_editor_mode()
                self.tprint("Switch editor mode to Compact mode Code \n")
                views.compact_json_data()

                self.tprint("Selecting editor mode \n")
                views.select_editor_mode_btn(1)
                self.tprint("Switch editor mode to Tree \n")
                views.switch_to_tree_editor_mode()

                self.tprint("Clicking on ArangoSearch documentation link \n")
                views.click_arangosearch_documentation_link()
                self.tprint("Selecting search option\n")
                views.select_inside_search("i")
                self.tprint("Traversing all results up and down \n")
                views.search_result_traverse_down()
                views.search_result_traverse_up()

                if self.is_cluster:
                    self.tprint('View rename is disabled in Cluster mode \n')
                else:
                    self.tprint("Rename firstViews to thirdViews started \n")
                    views.clicking_rename_views_btn()
                    views.rename_views_name("thirdView")
                    views.rename_views_name_confirm()
                    self.tprint("Rename the current Views completed \n")
                self.webdriver.back()

            # checking negative scenarios for all package version
            if (
                semver.VersionInfo.parse("3.8.100")
                < views.current_package_version()
                < semver.VersionInfo.parse("3.9.100")
                ):
                    views.checking_views_negative_scenario_for_views()

        except BaseException:
            self.tprint('x' * 45, "\nINFO: Error Occurred! Force Deletion Started\n", 'x' * 45)
            self.exception = True  # mark the exception as true
            self.error = traceback.format_exc()

        finally:
            # deleting views for <= v3.8.x
            if views.current_package_version() < semver.VersionInfo.parse("3.9.0"):
                self.tprint("Deleting views started for <= v3.8.x\n")
                views.delete_views("first_view", views.select_first_view_id)
                views.delete_views(
                    "renamed_view", views.select_renamed_view_id
                )
                views.delete_views("second_view", views.select_second_view_id)
                self.tprint("Deleting views completed for <= v3.8.x \n")

            # deleting views for v3.9.x
            elif (
                semver.VersionInfo.parse("3.8.100")
                < views.current_package_version()
                < semver.VersionInfo.parse("3.9.100")
            ):
                self.tprint("Views deletion started for >= v3.9.x \n")
                views.delete_views(
                    "improved_arangosearch_view_01",
                    views.select_improved_arangosearch_view_01,
                )
                views.delete_views(
                    "modified_views_name", views.select_modified_views_name
                )
                views.delete_views(
                    "improved_arangosearch_view_02",
                    views.select_improved_arangosearch_view_02,
                )
                self.tprint("Views deletion completed for >= v3.9.x \n")

            # deleting improved views for v3.10.x
            elif views.current_package_version() > semver.VersionInfo.parse("3.9.100"):
                self.tprint("Selecting Views tab\n")
                views.navbar_goto("views")

                if (
                    semver.VersionInfo.parse("3.9.100")
                    < views.current_package_version()
                    < semver.VersionInfo.parse("3.10.100")
                ):
                    self.tprint("Deleting views started for >= v3.10.x\n")
                    views.delete_views_310("improved_arangosearch_view_01")
                    views.delete_views_310("modified_views_name")
                    views.delete_views_310("improved_arangosearch_view_02")
                    views.delete_created_collection("views_collection")
                    self.tprint("Deleting views completed for >= v3.10.x\n")

                if views.current_package_version() >= semver.VersionInfo.parse("3.11.0"):
                    self.tprint("Deleting views started for >= v3.11.x\n")
                    views.delete_views_312("arangosearch_view_3111")
                    views.delete_views_312("arangosearch_view_3112")
                    # if views.current_package_version() > semver.VersionInfo.parse("3.11.100"):
                    #     views.delete_views_312("search_alias")

            del views
            self.tprint("---------Checking Views completed--------- \n")
            if self.exception:
                raise Exception(self.error)
