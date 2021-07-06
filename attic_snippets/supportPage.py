import time

from baseSelenium import BaseSelenium


class SupportPage(BaseSelenium):

    def __init__(self, driver):
        super().__init__()
        self.driver = driver
        self.select_support_page_id = "support"
        self.select_documentation_support_id = 'documentation-support'
        self.select_community_support_id = 'community-support'

    # creating graph manually
    def select_support_page(self):
        support = self.select_support_page_id
        support = \
            BaseSelenium.locator_finder_by_id(self, support)
        support.click()
        time.sleep(1)

    # selecting documentation support
    def select_documentation_support(self):
        documentation = self.select_documentation_support_id
        documentation = \
            BaseSelenium.locator_finder_by_id(self, documentation)
        documentation.click()
        time.sleep(1)

    # Clicking on link on any page and switch to that tab and return to origin tab
    def click_on_link(self, link_id):
        click_on_link_id = link_id
        click_on_link_id = \
            BaseSelenium.locator_finder_by_xpath(self, click_on_link_id)
        self.switch_tab(click_on_link_id)  # this method will call switch tab and close tab

    # this method will be loop through all the list links
    def loop_for_link_traversal(self, print_statement, link_list):
        i = 0
        while i < len(link_list):
            print(print_statement[i])
            self.click_on_link(link_list[i])
            i = i + 1

    # Clicking all the links on manual link tab
    def manual_link(self):
        print('Checking all arangodb manual link started\n')

        # link name for all the manual link
        getting_started = '//*[@id="documentation"]/div/div[2]/ul/li[1]/a'
        data_models_and_modelling = '//*[@id="documentation"]/div/div[2]/ul/li[2]/a'
        administration = '//*[@id="documentation"]/div/div[2]/ul/li[3]/a'
        scaling = '//*[@id="documentation"]/div/div[2]/ul/li[4]/a'
        graphs = '//*[@id="documentation"]/div/div[2]/ul/li[5]/a'
        go_to_manual_start_page = '//*[@id="documentation"]/div/div[2]/ul/li[6]/a'

        manual_link_list_print_statement = ['Checking Getting started link \n',
                                            'Checking Data models & modeling link \n',
                                            'Checking Administration link \n',
                                            'Checking Scaling link \n',
                                            'Checking Graphs link \n',
                                            'Checking Go to Manual start page link \n']

        manual_link_list = [getting_started, data_models_and_modelling,
                            administration, scaling, graphs, go_to_manual_start_page]

        self.loop_for_link_traversal(manual_link_list_print_statement, manual_link_list)

        print('Checking all arangodb manual link completed \n')

    # Clicking all the links on AQL Query Language link tab
    def aql_query_language_link(self):
        print('Checking all arangodb AQL Query Language link started\n')

        # link name for all the AQL Query link
        fundamentals = '//*[@id="documentation"]/div/div[3]/ul/li[1]/a'
        data_queries = '//*[@id="documentation"]/div/div[3]/ul/li[2]/a'
        functions = '//*[@id="documentation"]/div/div[3]/ul/li[3]/a'
        usual_query_patterns = '//*[@id="documentation"]/div/div[3]/ul/li[4]/a'
        go_to_aql_query_page = '//*[@id="documentation"]/div/div[3]/ul/li[5]/a'

        aql_link_list_print_statement = ['Checking Fundamentals link \n',
                                         'Checking Data Queries link \n',
                                         'Checking Functions link \n',
                                         'Checking Usual Query Patterns link \n',
                                         'Checking Go to AQL start page link \n']
        aql_link_list = [fundamentals, data_queries, functions, usual_query_patterns, go_to_aql_query_page]

        self.loop_for_link_traversal(aql_link_list_print_statement, aql_link_list)

        print('Checking all arangodb AQL Query Language link completed\n')

    # Clicking all the links on fox framework link tab
    def fox_framework_link(self):
        print('Checking all arangodb Fox Framework link started\n')

        # link name for all the fox framework link
        micro_service = '//*[@id="documentation"]/div/div[4]/ul/li[1]/a'
        guides = '//*[@id="documentation"]/div/div[4]/ul/li[2]/a'
        reference = '//*[@id="documentation"]/div/div[4]/ul/li[3]/a'
        deployment = '//*[@id="documentation"]/div/div[4]/ul/li[4]/a'
        go_to_fox_start = '//*[@id="documentation"]/div/div[4]/ul/li[5]/a'

        fox_framework_print_statement = ['Checking Micro Service link \n',
                                         'Checking Guides link \n',
                                         'Checking Reference link \n',
                                         'Checking Deployment link \n',
                                         'Checking Go to Foxx start page link \n']

        fox_framework_list = [micro_service, guides, reference, deployment, go_to_fox_start]

        self.loop_for_link_traversal(fox_framework_print_statement, fox_framework_list)

        print('Checking all arangodb Fox Framework link completed\n')

    # Clicking all the links official drivers and integration link tab
    def driver_and_integration_link(self):
        print('Checking all Drivers and Integration link started\n')

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

        self.loop_for_link_traversal(Official_print_statement, drivers_and_integration)

        print('Checking all arangodb Drivers and Integration link completed\n')

    # Checking community support link
    def community_support_link(self):
        print('Checking all Support tab link started\n')

        support = self.select_support_page_id
        support = \
            BaseSelenium.locator_finder_by_id(self, support)
        support.click()
        time.sleep(1)

        # selecting community support tab
        com_support = self.select_community_support_id
        com_support = \
            BaseSelenium.locator_finder_by_id(self, com_support)
        com_support.click()
        time.sleep(1)

        # all support tab link id
        paying_customer_support = '//*[@id="community"]/div/div[2]/a'
        github_issues = '//*[@id="community"]/div/div[4]/a'
        stack_overflow = '//*[@id="community"]/div/div[5]/a'
        slack = '//*[@id="community"]/div/div[6]/a'
        google_groups = '//*[@id="community"]/div/div[7]/a'
        arangodb_contact_us = '//*[@id="community"]/div/div[8]/a'

        support_tab_print_statement = ['Checking paying customer support link \n',
                                       'Checking Github issue report link \n',
                                       'Checking StackOverflow link \n',
                                       'Checking Slack Community link \n',
                                       'Checking ArangoDB Google group link \n',
                                       'Checking ArangoDB Contact Us link \n']

        # list for all the support link
        support_list = [paying_customer_support, github_issues, stack_overflow,
                        slack, google_groups, arangodb_contact_us]

        self.loop_for_link_traversal(support_tab_print_statement, support_list)

        print('Checking all Support tab link completed \n')
