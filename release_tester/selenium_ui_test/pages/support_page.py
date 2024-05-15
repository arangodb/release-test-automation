"""support page model"""
import time
import semver

from selenium_ui_test.pages.navbar import NavigationBarPage

# can't circumvent long lines.. nAttr nLines
# pylint: disable=C0301 disable=R0902 disable=R0915 disable=R0914
# pylint: disable=line-too-long disable=too-many-instance-attributes disable=too-many-statements disable=too-many-locals


class SupportPage(NavigationBarPage):
    """Class for Support page"""

    def __init__(self, driver, cfg):
        """Support page initialization"""
        super().__init__(driver, cfg)
        self.select_support_page_id = "support"
        self.select_documentation_support_id = "documentation-support"
        self.select_community_support_id = "community-support"
        self.select_rest_api_swagger_id = "swagger-support"
        self.switch_to_iframe_id = '//*[@id="swagger"]/iframe'

    def select_support_page(self):
        """Selecting support page"""
        support = self.select_support_page_id
        support = self.locator_finder_by_id(support)
        support.click()
        time.sleep(1)

    def select_documentation_support(self):
        """selecting documentation support"""
        documentation = self.select_documentation_support_id
        documentation = self.locator_finder_by_id(documentation)
        documentation.click()
        time.sleep(1)

    def click_on_link(self, link_id):
        """Clicking on link on any page and switch to that tab and return to origin tab"""
        click_on_link_id_sitem = self.locator_finder_by_xpath(link_id)
        title = self.switch_tab(click_on_link_id_sitem)  # this method will call switch tab and close tab
        return title

    def loop_through_link_traversal(self, print_statement, link_list, assertion_list):
        """this method will be loop through all the list links"""
        import time

        # Define the maximum number of retries
        max_retries = 3

        i = 0
        while i < len(link_list):
            print(print_statement[i])
            title = None
            try_count = 0
            
            # Attempt the operation up to max_retries times
            while try_count < max_retries:
                try:
                    title = self.click_on_link(link_list[i])
                    self.wait_for_ajax()
                    assert title == assertion_list[i], f"Expected page title {assertion_list[i]} but got {title}"
                    break  # If successful, break out of the retry loop
                except Exception as e:
                    # If an error occurs, print the error message
                    print(f"Error occurred: {e}")
                    
                    # Increment retry count
                    try_count += 1
                    
                    # If maximum retries reached, raise an error
                    if try_count == max_retries:
                        print(f"Failed after {max_retries} attempts for link: {link_list[i]}")
                        break  # Break out of the retry loop
                    
                    # Wait for a few seconds before retrying
                    time.sleep(3)
            
            # Move to the next link
            i += 1


    def click_on_btn(self, link_id):
        """this method will execute multiple backup restore tab documentation"""
        click_on_btn = link_id
        click_on_btn = self.locator_finder_by_xpath(click_on_btn)
        click_on_btn.click()

    def loop_through_btn_traversal(self, print_statement, btn_list):
        """this method will be loop through all the list buttons"""
        i = 0
        while i < len(btn_list):
            print(print_statement[i])
            self.click_on_btn(btn_list[i])
            i = i + 1
            if i == len(btn_list):
                print("Checking Backup Restore option completed \n")
            time.sleep(2)

    def manual_link(self):
        """Clicking all the links on manual link tab"""
        print("Checking all arangodb manual link started\n")

        # link name for all the manual link
        getting_started = '//*[@id="documentation"]/div/div[2]/ul/li[1]/a'
        data_models_and_modelling = '//*[@id="documentation"]/div/div[2]/ul/li[2]/a'
        administration = '//*[@id="documentation"]/div/div[2]/ul/li[3]/a'
        scaling = '//*[@id="documentation"]/div/div[2]/ul/li[4]/a'
        graphs = '//*[@id="documentation"]/div/div[2]/ul/li[5]/a'
        go_to_manual_start_page = '//*[@id="documentation"]/div/div[2]/ul/li[6]/a'

        manual_link_list_print_statement = [
            "Checking Getting started link \n",
            "Checking Data models & modeling link \n",
            "Checking Administration link \n",
            "Checking Scaling link \n",
            "Checking Graphs link \n",
            "Checking Go to Manual start page link \n",
        ]

        manual_link_list = [
            getting_started,
            data_models_and_modelling,
            administration,
            scaling,
            graphs,
            go_to_manual_start_page,
        ]

        if self.version_is_newer_than("3.11.99"):
            manual_link_assertion_check = ['Get Started | ArangoDB Documentation',
                                           'Data Models | ArangoDB Documentation',
                                           'Administration | ArangoDB Documentation',
                                           'The scalability of ArangoDB and its data models | ArangoDB Documentation',
                                           'Graphs | ArangoDB Documentation',
                                           'Recommended Resources | ArangoDB Documentation']
        else:
            manual_link_assertion_check = ['Getting Started | Manual | ArangoDB Documentation',
                                           'Modeling Data for ArangoDB | ArangoDB Documentation',
                                           'Administration | Manual | ArangoDB Documentation',
                                           'Scaling | Manual | ArangoDB Documentation',
                                           'Graphs | Manual | ArangoDB Documentation',
                                           'Introduction to ArangoDB Documentation | ArangoDB Documentation']

        self.loop_through_link_traversal(
            manual_link_list_print_statement, manual_link_list, manual_link_assertion_check
        )

        print("Checking all arangodb manual link completed \n")

    def aql_query_language_link(self):
        """Clicking all the links on AQL Query Language link tab"""
        print("Checking all arangodb AQL Query Language link started\n")

        # link name for all the AQL Query link
        fundamentals = '//*[@id="documentation"]/div/div[3]/ul/li[1]/a'
        data_queries = '//*[@id="documentation"]/div/div[3]/ul/li[2]/a'
        functions = '//*[@id="documentation"]/div/div[3]/ul/li[3]/a'
        usual_query_patterns = '//*[@id="documentation"]/div/div[3]/ul/li[4]/a'
        go_to_aql_query_page = '//*[@id="documentation"]/div/div[3]/ul/li[5]/a'

        aql_link_list_print_statement = [
            "Checking Fundamentals link \n",
            "Checking Data Queries link \n",
            "Checking Functions link \n",
            "Checking Usual Query Patterns link \n",
            "Checking Go to AQL start page link \n",
        ]
        aql_link_list = [fundamentals, data_queries, functions, usual_query_patterns, go_to_aql_query_page]

        if self.version_is_newer_than("3.11.99"):
            fundamental_link_assertion_check = ['AQL Fundamentals | ArangoDB Documentation',
                                                'AQL Data Queries | ArangoDB Documentation',
                                                'AQL functions | ArangoDB Documentation',
                                                'AQL Query Patterns and Examples | ArangoDB Documentation',
                                                'AQL Documentation | ArangoDB Documentation']
        else:
            fundamental_link_assertion_check = ['AQL Fundamentals | AQL | ArangoDB Documentation',
                                                'AQL Data Queries | ArangoDB Documentation',
                                                'ArangoDB Query Language AQL Functions | ArangoDB Documentation',
                                                'AQL Query Patterns & Examples | ArangoDB Documentation',
                                                'ArangoDB Query Language (AQL) Introduction | ArangoDB Documentation']

        self.loop_through_link_traversal(aql_link_list_print_statement, aql_link_list, fundamental_link_assertion_check)

        print("Checking all arangodb AQL Query Language link completed\n")

    def fox_framework_link(self):
        """Clicking all the links on fox framework link tab"""
        print("Checking all arangodb Fox Framework link started\n")

        # link name for all the fox framework link
        micro_service = '//*[@id="documentation"]/div/div[4]/ul/li[1]/a'
        guides = '//*[@id="documentation"]/div/div[4]/ul/li[2]/a'
        reference = '//*[@id="documentation"]/div/div[4]/ul/li[3]/a'
        deployment = '//*[@id="documentation"]/div/div[4]/ul/li[4]/a'
        go_to_fox_start = '//*[@id="documentation"]/div/div[4]/ul/li[5]/a'

        fox_framework_print_statement = [
            "Checking Micro Service link \n",
            "Checking Guides link \n",
            "Checking Reference link \n",
            "Checking Deployment link \n",
            "Checking Go to Foxx start page link \n",
        ]

        fox_framework_list = [micro_service, guides, reference, deployment, go_to_fox_start]

        if self.version_is_newer_than("3.11.99"):
            fox_framework_assertion_Check = ['Getting Started | ArangoDB Documentation',
                                             'Guides | ArangoDB Documentation',
                                             'Foxx reference | ArangoDB Documentation',
                                             'Deployment | ArangoDB Documentation',
                                             'Foxx Microservices | ArangoDB Documentation']
        else:
            fox_framework_assertion_Check = ['Getting started | Foxx Microservices | Manual | ArangoDB Documentation',
                                             'Guides | Foxx Microservices | Manual | ArangoDB Documentation',
                                             'Reference | Foxx Microservices | Manual | ArangoDB Documentation',
                                             'Deployment | Foxx Microservices | Manual | ArangoDB Documentation',
                                             'Foxx Microservices | ArangoDB Documentation']

        self.loop_through_link_traversal(fox_framework_print_statement, fox_framework_list, fox_framework_assertion_Check)

        print("Checking all arangodb Fox Framework link completed\n")

    def driver_and_integration_link(self):
        """Clicking all the links official drivers and integration link tab"""
        print("Checking all Drivers and Integration link started\n")

        if self.version_is_newer_than("3.11.99"):
            # link name for all the Drivers and Integration link
            arangodb_java_driver = '//*[@id="documentation"]/div/div[5]/ul/li[1]/a'
            arangojs_java_script = '//*[@id="documentation"]/div/div[5]/ul/li[2]/a'
            arangodb_go_driver = '//*[@id="documentation"]/div/div[5]/ul/li[3]/a'
            arangodb_spring_data = '//*[@id="documentation"]/div/div[5]/ul/li[4]/a'
            arangodb_spark_connector = '//*[@id="documentation"]/div/div[5]/ul/li[5]/a'
            drivers_and_integration = '//*[@id="documentation"]/div/div[5]/ul/li[6]/a'

            Official_print_statement = ['Checking ArangoDB Java Driver link \n',
                                        'Checking ArangoJS - Javascript Driver link \n',
                                        'Checking ArangoDB Go driver link \n',
                                        'Checking Go to ArangoDB Spring Data page link \n',
                                        'Checking Go to ArangoDB Spark Connections page link \n',
                                        'Checking Go to Drivers and Integration start page link\n']

            drivers_and_integration = [arangodb_java_driver, arangojs_java_script, arangodb_php, arangodb_go_driver,
                                       arangodb_spring_data, drivers_and_integration]

            driver_integration_assertion_check = ['ArangoDB Java driver | ArangoDB Documentation',
                                                  'ArangoDB Node.js driver | ArangoDB Documentation',
                                                  'ArangoDB Go driver | ArangoDB Documentation',
                                                  'Spring Data ArangoDB | ArangoDB Documentation',
                                                  'ArangoDB Datasource for Apache Spark | ArangoDB Documentation',
                                                  'Official ArangoDB drivers | ArangoDB Documentation']
        else:
            # link name for all the Drivers and Integration link
            arangodb_java_driver = '//*[@id="documentation"]/div/div[5]/ul/li[1]/a'
            arangojs_java_script = '//*[@id="documentation"]/div/div[5]/ul/li[2]/a'
            arangodb_php = '//*[@id="documentation"]/div/div[5]/ul/li[3]/a'
            arangodb_go_driver = '//*[@id="documentation"]/div/div[5]/ul/li[4]/a'
            arangodb_spring_data = '//*[@id="documentation"]/div/div[5]/ul/li[5]/a'
            arangodb_spark_connector = '//*[@id="documentation"]/div/div[5]/ul/li[6]/a'
            driver_and_integration = '//*[@id="documentation"]/div/div[5]/ul/li[7]/a'

            Official_print_statement = ['Checking ArangoDB Java Driver link \n',
                                        'Checking ArangoJS - Javascript Driver link \n',
                                        'Checking ArangoDB-PHP link \n',
                                        'Checking ArangoDB Go Driver link \n',
                                        'Checking Go to ArangoDB Spring Data page link \n',
                                        'Checking Go to ArangoDB Spark Connections page link\n',
                                        'Checking Go to Drivers & Integrations start page link \n']

            drivers_and_integration = [arangodb_java_driver, arangojs_java_script, arangodb_php, arangodb_go_driver,
                                       arangodb_spring_data, arangodb_spark_connector, driver_and_integration]

            driver_integration_assertion_check = ['Java Driver | Drivers | ArangoDB Documentation',
                                                  'ArangoDB JavaScript Driver | ArangoDB Documentation',
                                                  'ArangoDB-PHP | Drivers | ArangoDB Documentation',
                                                  'ArangoDB Go Driver | Drivers | ArangoDB Documentation',
                                                  'Spring Data ArangoDB | Drivers | ArangoDB Documentation',
                                                  'ArangoDB Spark Connector | Drivers | ArangoDB Documentation',
                                                  'Install Official Drivers, Integrations and Community Drivers | '
                                                  'ArangoDB Documentation']

        self.loop_through_link_traversal(Official_print_statement, drivers_and_integration,
                                         driver_integration_assertion_check)

        print('Checking all arangodb Drivers and Integration link completed\n')

    def community_support_link(self):
        """Checking community support link"""
        print("Checking all Support tab link started\n")

        support = self.select_support_page_id
        support = self.locator_finder_by_id(support)
        support.click()
        time.sleep(1)

        # selecting community support tab
        com_support = self.select_community_support_id
        com_support = self.locator_finder_by_id(com_support)
        com_support.click()
        time.sleep(1)

        # all support tab link id
        paying_customer_support = '//*[@id="community"]/div/div[2]/a'
        github_issues = '//*[@id="community"]/div/div[4]/a'
        stack_overflow = '//*[@id="community"]/div/div[5]/a'
        slack = '//*[@id="community"]/div/div[6]/a'
        google_groups = '//*[@id="community"]/div/div[7]/a'
        arangodb_contact_us = '//*[@id="community"]/div/div[8]/a'

        support_tab_print_statement = [
            "Checking paying customer support link \n",
            "Checking Github issue report link \n",
            "Checking StackOverflow link \n",
            "Checking Slack Community link \n",
            "Checking ArangoDB Google group link \n",
            "Checking ArangoDB Contact Us link \n",
        ]

        # list for all the support link
        support_list = [
            paying_customer_support,
            github_issues,
            stack_overflow,
            slack,
            google_groups,
            arangodb_contact_us,
        ]

        if self.version_is_newer_than("3.11.99"):
            support_link_assertion_check = ["Jira Service Management",
                                            "GitHub - arangodb/arangodb: 🥑 ArangoDB is a native multi-model database "
                                            "with flexible data models for documents, graphs, and key-values. Build high "
                                            "performance applications using a convenient SQL-like query language or "
                                            "JavaScript extensions.",
                                            "Newest 'arangodb' Questions - Stack Overflow",
                                            "Slack",
                                            "Redirecting to Google Groups",
                                            "contact - ArangoDB"]
        else:
            support_link_assertion_check = ["ArangoDB - Jira Service Management",
                                            "GitHub - arangodb/arangodb: 🥑 ArangoDB is a native multi-model database "
                                            "with flexible data models for documents, graphs, and key-values. Build high "
                                            "performance applications using a convenient SQL-like query language or "
                                            "JavaScript extensions.",
                                            "Newest 'arangodb' Questions - Stack Overflow",
                                            "Join ArangoDB Community on Slack!",
                                            "Redirecting to Google Groups",
                                            "Contact - ArangoDB"]

        self.loop_through_link_traversal(support_tab_print_statement, support_list, support_link_assertion_check)

        print("Checking all Support tab link completed \n")

    def rest_api(self):
        """Checking all rest api swagger link"""
        print("Checking all Rest api tab link started\n")

        support = self.select_support_page_id
        support = self.locator_finder_by_id(support)
        support.click()
        time.sleep(1)

        # selecting community support tab
        rest_api = self.select_rest_api_swagger_id
        rest_api = self.locator_finder_by_id(rest_api)
        rest_api.click()
        time.sleep(1)

        if self.current_package_version() >= semver.VersionInfo.parse("3.7.0"):
            # checking backup restore
            iframe = self.switch_to_iframe_id
            self.switch_to_iframe(iframe)

            print("Checking Backup Restore option started\n")
            backup_restore = '//*[@id="operations-tag-BackupRestore"]'
            backup_restore = self.locator_finder_by_xpath(backup_restore)
            backup_restore.click()
            time.sleep(1)

        # all documentation example list for Backup restore option
        create_backup = "(//span[contains(text(),'POST')])[1]"
        delete_backup = "(//span[contains(text(),'POST')])[2]"
        download_backup = "(//span[contains(text(),'POST')])[3]"
        list_backup = "(//span[contains(text(),'POST')])[4]"
        restore_backup = "(//span[contains(text(),'POST')])[5]"
        upload_remote_repository = "(//span[contains(text(),'POST')])[6]"

        # making a list out of these documentation list
        backup_restore_list = [
            create_backup,
            create_backup,
            delete_backup,
            delete_backup,
            download_backup,
            download_backup,
            list_backup,
            list_backup,
            restore_backup,
            restore_backup,
            upload_remote_repository,
            upload_remote_repository,
        ]

        backup_restore_print_statement = [
            "Checking create backup \n",
            "Checking create backup completed\n",
            "Checking delete backup button \n",
            "Checking delete backup button completed\n",
            "Checking list backup button\n",
            "Checking list backup button completed\n",
            "Checking download backup button \n",
            "Checking download backup button completed\n",
            "Checking restore backup button \n",
            "Checking restore backup button completed\n",
            "Checking upload backup to remote repository button \n",
            "Checking upload backup to remote repository button completed\n",
        ]

        self.loop_through_btn_traversal(backup_restore_print_statement, backup_restore_list)
        # print('Checking Backup Restore option started\n')

        # switching back to default view
        self.switch_back_to_origin_window()
