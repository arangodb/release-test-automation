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
        print("---------Checking Views Begin--------- \n")
        views = ViewsPage(self.webdriver, self.cfg)  # creating obj for viewPage
        assert views.current_user() == "ROOT", "current user is root?"
        assert views.current_database() == "_SYSTEM", "current database is _system?"

        self.exception = False
        self.error = None

        try:
            print("Selecting Views tab\n")
            views.select_views_tab()

            # creating v3.9.x and v3.10.x for improved views
            if views.current_package_version() >= semver.VersionInfo.parse("3.9.0"):
                print('Creating improved views start here \n')
                views.create_improved_views('improved_arangosearch_view_01', 0)
                self.webdriver.refresh()
                time.sleep(4)
                views.create_improved_views('improved_arangosearch_view_02', 1)
                print('Creating improved views completed \n')

                # Checking improved views for v3.9.x
                if semver.VersionInfo.parse("3.8.100") < views.current_package_version() < semver.VersionInfo.parse(
                        "3.9.100"):
                    views.checking_improved_views('improved_arangosearch_view_01',
                                                       views.select_improved_arangosearch_view_01, self.is_cluster)
                 
                 # Checking improved views for v3.10.x
                if views.current_package_version() > semver.VersionInfo.parse("3.9.100"):
                    views.checking_improved_views_for_v310('improved_arangosearch_view_01',
                                                                self.views.select_improved_arangosearch_view_01,
                                                                self.deployment)


            elif views.current_package_version() <= semver.VersionInfo.parse("3.8.100"):
                views.create_new_views('firstView')
                views.create_new_views('secondView')

                views.select_views_settings()
                print("Sorting views to descending\n")
                views.select_sorting_views()
                print("Sorting views to ascending\n")
                views.select_sorting_views()

                print("search views option testing\n")
                views.search_views("secondView", views.search_second_view)
                views.search_views("firstView", views.search_first_view)

                print("Selecting first Views \n")
                views.select_first_view()
                print("Selecting collapse button \n")
                views.select_collapse_btn()
                print("Selecting expand button \n")
                views.select_expand_btn()
                print("Selecting editor mode \n")
                views.select_editor_mode_btn(0)
                print("Switch editor mode to Code \n")
                views.switch_to_code_editor_mode()
                print("Switch editor mode to Compact mode Code \n")
                views.compact_json_data()

                print("Selecting editor mode \n")
                views.select_editor_mode_btn(1)
                print("Switch editor mode to Tree \n")
                views.switch_to_tree_editor_mode()

                print("Clicking on ArangoSearch documentation link \n")
                views.click_arangosearch_documentation_link()
                print("Selecting search option\n")
                views.select_inside_search("i")
                print("Traversing all results up and down \n")
                views.search_result_traverse_down()
                views.search_result_traverse_up()

                if self.is_cluster:
                    print('View rename is disabled in Cluster mode \n')
                else:
                    print("Rename firstViews to thirdViews started \n")
                    views.clicking_rename_views_btn()
                    views.rename_views_name("thirdView")
                    views.rename_views_name_confirm()
                    print("Rename the current Views completed \n")
                self.webdriver.back()

            # checking negative scenarios for all package version
            views.checking_views_negative_scenario_for_views()

        except BaseException:
            print('x' * 45, "\nINFO: Error Occurred! Force Deletion Started\n", 'x' * 45)
            self.exception = True  # mark the exception as true
            self.error = traceback.format_exc()

        finally:
            # deleting views for <= v3.8.x
            if views.current_package_version() < semver.VersionInfo.parse("3.9.0"):
                print("Deleting views started for <= v3.8.x\n")
                views.delete_views('first_view', views.select_first_view_id)
                views.delete_views('renamed_view', views.select_renamed_view_id)
                views.delete_views('second_view', views.select_second_view_id)
                print('Deleting views completed for <= v3.8.x \n')

            elif semver.VersionInfo.parse("3.8.100") < views.current_package_version() \
                    < semver.VersionInfo.parse("3.9.100"):
                print("I am here in line 371 \n")
                print("Views deletion started for >= v3.9.x \n")
                views.delete_views('improved_arangosearch_view_01',
                                        views.select_improved_arangosearch_view_01)
                views.delete_views('modified_views_name', views.select_modified_views_name)
                views.delete_views('improved_arangosearch_view_02',
                                        views.select_improved_arangosearch_view_02)
                print("Views deletion completed for >= v3.9.x \n")

            # deleting improved views for v3.10.x
            elif views.current_package_version() > semver.VersionInfo.parse("3.9.100"):
                # self.views.checking_modified_views(self.deployment)
                print("Selecting Views tab\n")
                views.select_views_tab()

                print('Deleting views started for >= v3.10.x\n')
                views.delete_new_views('improved_arangosearch_view_01')
                views.delete_new_views('modified_views_name')
                views.delete_new_views('improved_arangosearch_view_02')
                print('Deleting views completed for >= v3.10.x\n')

            del views
            print("---------Checking Views completed--------- \n")
            if self.exception:
                raise Exception(self.error)
