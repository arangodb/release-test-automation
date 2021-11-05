from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase
from selenium_ui_test.pages.views_page import ViewsPage


class ViewsTestSuite(BaseTestSuite):
    @testcase
    def test_views(self):
        """testing Views page"""
        print("---------Checking Views Begin--------- \n")
        # login = LoginPage(self.webdriver)
        # login.login('root', self.root_passvoid)
        views = ViewsPage(self.webdriver)  # creating obj for viewPage
        assert views.current_user() == "ROOT", "current user is root?"
        assert views.current_database() == "_SYSTEM", "current database is _system?"

        print("Selecting Views tab\n")
        views.select_views_tab()

        # checking 3.9 for improved views
        version = views.current_package_version()

        if version == 3.9:
            print("Creating improved views start here \n")
            views.create_improved_views("improved_arangosearch_view_01", 0)
            views.create_improved_views("improved_arangosearch_view_02", 1)
            print("Creating improved views completed \n")

            # Checking improved views
            views.checking_improved_views(
                "improved_arangosearch_view", views.select_improved_arangosearch_view_01, self.is_cluster
            )

            print("Deleting views started \n")
            if self.is_cluster:
                views.delete_views("improved_arangosearch_view_01", views.select_improved_arangosearch_view_01)
            else:
                views.delete_views("modified_views_name", views.select_modified_views_name)
            views.delete_views("improved_arangosearch_view_02", views.select_improved_arangosearch_view_02)
            print("Deleting views completed \n")

        # for package version less than 3.9e
        elif version <= 3.9:
            views.create_new_views("firstView")
            views.create_new_views("secondView")

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
            views.select_editor_mode_btn()
            print("Switch editor mode to Code \n")
            views.switch_to_code_editor_mode()
            print("Switch editor mode to Compact mode Code \n")
            views.compact_json_data()

            print("Selecting editor mode \n")
            views.select_editor_mode_btn()
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
                print("View rename is disabled in Cluster mode \n")
            else:
                print("Rename firstViews to thirdViews started \n")
                views.clicking_rename_views_btn()
                views.rename_views_name("thirdView")
                views.rename_views_name_confirm()
                print("Rename the current Views completed \n")

            print("Deleting views started \n")
            if self.is_cluster:
                views.delete_views("first_view", views.select_first_view_id)
            else:
                views.delete_views("renamed_view", views.select_renamed_view_id)

            views.delete_views("second_view", views.select_second_view_id)

        # print("Deleting views completed\n")
        del views
        print("---------Checking Views completed--------- \n")
