from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase
from selenium_ui_test.pages.views_page import ViewsPage


class ViewsTestSuite(BaseTestSuite):
    @testcase
    def test_views(self):
        """testing Views page"""
        print("---------Checking Views Begin--------- \n")
        #login = LoginPage(self.webdriver)
        #login.login('root', self.root_passvoid)
        views = ViewsPage(self.webdriver)  # creating obj for viewPage
        views1 = ViewsPage(self.webdriver)  # creating 2nd obj for viewPage to do counter part of the testing

        print("Selecting Views tab\n")
        views.select_views_tab()
        print("Creating first views\n")
        views.create_new_views()
        views.naming_new_view("firstView")
        views.select_create_btn()
        print("Creating first views completed\n")

        print("Creating second views\n")
        views1.create_new_views()
        views1.naming_new_view("secondView")
        views1.select_create_btn()
        print("Creating second views completed\n")

        views.select_views_settings()
        print("Sorting views to descending\n")
        views.select_sorting_views()

        print("Sorting views to ascending\n")
        views1.select_sorting_views()

        print("search views option testing\n")
        views1.search_views("se")
        views.search_views("fi")

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
        views1.select_editor_mode_btn()
        print("Switch editor mode to Tree \n")
        views1.switch_to_tree_editor_mode()

        print("Clicking on ArangoSearch documentation link \n")
        views.click_arangosearch_documentation_link()
        print("Selecting search option\n")
        views.select_inside_search("i")
        print("Traversing all results up and down \n")
        views.search_result_traverse_down()
        views.search_result_traverse_up()
        views1.select_inside_search("")
        # ###print("Changing views consolidationPolicy id to 55555555 \n")
        # ###views1.change_consolidation_policy(55555555)
        if not self.is_cluster:
            print("Rename firstViews to thirdViews started \n")
            views.clicking_rename_views_btn()
            views.rename_views_name("thirdView")
            views.rename_views_name_confirm()
            print("Rename the current Views completed \n")
            self.webdriver.back()
            print("Deleting views started \n")
            views.select_renamed_view()
        else:
            print("Deleting views started \n")
            views.select_views_tab()
            views.select_first_view()
        views.delete_views_btn()
        views.delete_views_confirm_btn()
        views.final_delete_confirmation()

        views1.select_second_view()
        views1.delete_views_btn()
        views1.delete_views_confirm_btn()
        views1.final_delete_confirmation()
        print("Deleting views completed\n")
        #login.logout_button()
        #del login
        del views
        del views1
        print("---------Checking Views completed--------- \n")