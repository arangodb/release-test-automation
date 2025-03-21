#!/usr/bin/env python3
""" service page object """
import time
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException

from selenium_ui_test.pages.navbar import NavigationBarPage

# pylint: disable=too-many-statements disable=too-many-locals disable=too-many-branches

class ServicePage(NavigationBarPage):
    """service page object"""
    # pylint: disable=too-many-instance-attributes
    #def __init__(self, driver, cfg, video_start_time):
    #super().__init__(driver, cfg, video_start_time)

    def select_service_page(self):
        """Selecting service page"""
        self.navbar_goto("services")

    def select_add_service_button(self):
        """selecting new service button"""
        if self.version_is_newer_than("3.11.100"):
            add_new_service = "(//button[normalize-space()='Add service'])[1]"
            add_new_service_sitem = self.locator_finder_by_xpath(add_new_service, benchmark=True)
        else:
            add_new_service = "addApp"
            add_new_service_sitem = self.locator_finder_by_id(add_new_service, benchmark=True)

        add_new_service_sitem.click()
        time.sleep(2)

    def service_search_option(self, search_keyword):
        """checking service page search options"""
        search = 'foxxSearch'
        service_search_sitem = self.locator_finder_by_id(search)
        service_search_sitem.click()
        service_search_sitem.clear()
        time.sleep(2)

        self.tprint(f'Searching for {search_keyword} \n')
        service_search_sitem.send_keys(search_keyword)
        time.sleep(1)

        # checking search find the correct demo services
        if search_keyword == 'demo':
            search_item = "//*[text()='demo-graphql']"
            expected_text = 'demo-graphql'
            demo_graphql_sitem = self.locator_finder_by_xpath(search_item)
            assert demo_graphql_sitem.text == expected_text, f"Expected text {expected_text} " \
                                                             f"but got {demo_graphql_sitem.text}"
        if search_keyword == 'tab':
            search_item = "//*[text()='tableau-connector']"
            expected_text = 'tableau-connector'
            demo_graphql_sitem = self.locator_finder_by_xpath(search_item)
            assert demo_graphql_sitem.text == expected_text, f"Expected text {expected_text} " \
                                                             f"but got {demo_graphql_sitem.text}"
        if search_keyword == 'grafana':
            search_item = "//*[text()='grafana-connector']"
            expected_text = 'grafana-connector'
            demo_graphql_sitem = self.locator_finder_by_xpath(search_item)
            assert demo_graphql_sitem.text == expected_text, f"Expected text {expected_text} " \
                                                             f"but got {demo_graphql_sitem.text}"

    def service_category_option(self):
        """checking service page category options"""
        category = 'categorySelection'

        self.tprint('Selecting category options \n')
        select_service_category_sitem = self.locator_finder_by_id(category)
        select_service_category_sitem.click()
        time.sleep(1)

    def service_filter_category_option(self):
        """selecting category search option"""
        filter_option = 'Category-filter'
        filter_option_sitem = self.locator_finder_by_xpath(filter_option)
        filter_option_sitem.click()
        filter_option_sitem.clear()
        time.sleep(1)

    def select_category_option_from_list(self, category):
        """checking service page category options"""
        if category == "connector":
            self.tprint(f"Selecting {category} category from the drop-down menu \n")
            connector_name = '//*[@id="connector-option"]/span[3]'
            connector_sitem = self.locator_finder_by_xpath(connector_name)
            connector_sitem.click()
            time.sleep(1)
            connector_sitem.click()

        if category == "service":
            self.tprint(f"Selecting {category} category from the drop-down menu \n")
            connector_name = '//*[@id="service-option"]/span[3]'
            connector_sitem = self.locator_finder_by_xpath(connector_name)
            connector_sitem.click()
            time.sleep(1)
            connector_sitem.click()

        if category == "geo":
            self.tprint(f"Selecting {category} category from the drop-down menu \n")
            connector_name = '//*[@id="geo-option"]/span[3]'
            connector_sitem = self.locator_finder_by_xpath(connector_name)
            connector_sitem.click()
            time.sleep(1)
            connector_sitem.click()

        if category == "demo":
            self.tprint(f"Selecting {category} category from the drop-down menu \n")
            connector_name = '//*[@id="demo-option"]/span[3]'
            connector_sitem = self.locator_finder_by_xpath(connector_name)
            connector_sitem.click()
            time.sleep(1)
            connector_sitem.click()

        if category == "graphql":
            self.tprint(f"Selecting {category} category from the drop-down menu \n")
            connector_name = '//*[@id="graphql-option"]/span[3]'
            connector_sitem = self.locator_finder_by_xpath(connector_name)
            connector_sitem.click()
            time.sleep(1)
            connector_sitem.click()

        if self.version_is_newer_than("3.11.99"):
            self.tprint("prometheus and monitoring is gone from >3.11.99 \n")
        else:
            if category == "prometheus":
                self.tprint(f"Selecting {category} category from the drop-down menu \n")
                connector_name = '//*[@id="prometheus-option"]/span[3]'
                connector_sitem = self.locator_finder_by_xpath(connector_name)
                connector_sitem.click()
                time.sleep(1)
                connector_sitem.click()

            if category == "monitoring":
                self.tprint(f"Selecting {category} category from the drop-down menu \n")
                connector_name = '//*[@id="monitoring-option"]/span[3]'
                connector_sitem = self.locator_finder_by_xpath(connector_name)
                connector_sitem.click()
                time.sleep(1)
                connector_sitem.click()

    def select_category_option_search_filter(self, keyword):
        """checking service page category option's filter option"""
        filter_placeholder = 'Category-filter'
        filter_placeholder_sitem = self.locator_finder_by_id(filter_placeholder)
        filter_placeholder_sitem.click()
        filter_placeholder_sitem.clear()
        filter_placeholder_sitem.send_keys(keyword)
        time.sleep(1)

        if keyword == 'geo':
            search_category = '//*[@id="geo-option"]/span[3]'
            search_category_sitem = self.locator_finder_by_xpath(search_category)
            expected_text = 'geo'
            assert search_category_sitem.text == expected_text, f"Expected text {expected_text} " \
                                                                f"but got {search_category_sitem.text}"

        if keyword == 'demo':
            search_category = '//*[@id="demo-option"]/span[3]'
            search_category_sitem = self.locator_finder_by_xpath(search_category)
            expected_text = 'demo'
            assert search_category_sitem.text == expected_text, f"Expected text {expected_text} " \
                                                                f"but got {search_category_sitem.text}"

        if keyword == 'connector':
            search_category = '//*[@id="connector-option"]/span[3]'
            search_category_sitem = self.locator_finder_by_xpath(search_category)
            expected_text = 'connector'
            assert search_category_sitem.text == expected_text, f"Expected text {expected_text} " \
                                                                f"but got {search_category_sitem.text}"

    def select_demo_geo_s2_service(self, max_retries=3):
        """Selecting demo geo s2 service from the list"""
        # XPath expression to locate the 'demo-geo-s2' service
        self.select_add_service_button()

        geo_service = "//*[text()='demo-geo-s2']"

        for attempt in range(max_retries):
            try:
                # Refresh the page only after the first attempt
                if attempt > 0:
                    self.webdriver.refresh()
                    self.wait_for_ajax()

                # Logging the attempt to select the service
                self.tprint('Selecting demo_geo_s2 service \n')

                # Finding the service element, with benchmarking on the first attempt
                geo_service_sitem = self.locator_finder_by_xpath(geo_service, benchmark=attempt == 0)

                # Clicking on the located service element
                geo_service_sitem.click()

                # Wait briefly to ensure the click action is processed
                time.sleep(2)

                # Return the element if successfully clicked
                return geo_service_sitem
            except TimeoutException as e:
                # Handle TimeoutException and log progress
                self.progress(f"Attempt {attempt + 1}: TimeoutException - {e}, retrying...")
            except NoSuchElementException as e:
                # Handle NoSuchElementException and log progress
                self.progress(f"Attempt {attempt + 1}: NoSuchElementException - {e}, retrying...")
            except ElementNotInteractableException as e:
                # Handle ElementNotInteractableException and log progress
                self.progress(f"Attempt {attempt + 1}: ElementNotInteractableException - {e}, retrying...")
                time.sleep(0.5)

        # Raise an exception if the element could not be found after the maximum number of attempts
        raise Exception("Failed to select demo_geo_s2 service after multiple attempts.")


    def checking_demo_geo_s2_service_github(self):
        """checking general stuff of demo_geo_s2 service"""
        self.webdriver.refresh()
        time.sleep(1)
        self.select_demo_geo_s2_service()
        github_link = "//*[text()='demo-geo-s2']"
        github_link_sitem = self.locator_finder_by_xpath(github_link)
        page_title = super().switch_tab(github_link_sitem)

        expected_title = 'GitHub - arangodb-foxx/demo-geo-s2: A Foxx based geo ' \
                         'example using the new (v3.4+) s2 geospatial index'

        assert page_title == expected_title, f"Expected text {expected_title} but got {page_title}"
        self.webdriver.back()

    def install_demo_geo_s2_service(self, mount_path, ui_data_dir):
        """Installing demo geo s2 service from the list"""
        self.webdriver.refresh()
        self.wait_for_ajax()

        self.navbar_goto("queries") # go to queries page
        self.wait_for_ajax()
        self.navbar_goto("services") # go to services page

        self.select_demo_geo_s2_service()

        self.tprint('Installing demo_geo_s2 service \n')
        service = 'installService'
        service_sitem = self.locator_finder_by_id(service)
        service_sitem.click()
        time.sleep(2)

        self.tprint(f'Selecting service mount point at {mount_path} \n')
        mount_point = "/html//input[@id='new-app-mount']"
        mount_point_sitem = self.locator_finder_by_xpath(mount_point, benchmark=True)
        mount_point_sitem.click()
        mount_point_sitem.clear()
        mount_point_sitem.send_keys(mount_path)

        # selecting install button
        self.tprint('Selecting install button \n')
        install_btn = 'modalButton1'
        install_btn_sitem = self.locator_finder_by_id(install_btn, benchmark=True)
        install_btn_sitem.click()
        time.sleep(6)
        self.webdriver.refresh()
        self.wait_for_ajax()
        self.navbar_goto("services")

        if self.version_is_newer_than("3.10.100"):
            # TODO
            self.tprint('skipped for now\n')
        else:
            # checking service has been created successfully
            if self.version_is_newer_than("3.11.100"):
                success = "(//td[normalize-space()='demo-geo-s2'])[1]"
            else:
                success = "//*[text()='demo-geo-s2']"

            try:
                success_sitem = self.locator_finder_by_xpath(success).text
                if success_sitem == 'demo-geo-s2':
                    self.tprint(f"{success_sitem} has been successfully created \n")
                    status = True
                else:
                    self.tprint('Could not locate the desired service! refreshing the UI \n')
                    self.webdriver.refresh()
                    time.sleep(1)
                    success_sitem = self.locator_finder_by_xpath(success).text
                    if success_sitem == 'demo-geo-s2':
                        self.tprint(f"{success_sitem} has been successfully created \n")
                        status = True
                    else:
                        status = False
                    time.sleep(2)

                # populating collections with necessary data
                if status:
                    # got to collection tab
                    self.navbar_goto("collections")
                    self.wait_for_ajax()
                    self.webdriver.refresh()
                    time.sleep(2)

                    # looking for default collection has been created or not
                    neighbourhood_collection = "//*[text()='neighborhoods']"
                    neighbourhoods_collection_sitem = self.locator_finder_by_xpath(
                        neighbourhood_collection
                    )

                    if neighbourhoods_collection_sitem.text == "neighborhoods":
                        self.tprint("open it and populate necessary data into it \n")
                        neighbourhoods_collection_sitem.click()

                        # selecting content submenu
                        content = "//div[@id='subNavigationBar']/ul[2]//a[.='Content']"
                        content_sitem = self.locator_finder_by_xpath(content)
                        content_sitem.click()
                        time.sleep(1)

                        self.tprint('select upload button \n')
                        upload = '//*[@id="importCollection"]/span/i'
                        self.locator_finder_by_xpath(upload).click()
                        time.sleep(1)

                        path1 = ui_data_dir / "ui_data" / "service_page" / "demo_geo_s2" / "neighborhoods.json"
                        self.tprint(f'Providing neighborhood collection path {path1} \n')
                        choose_file_btn = 'importDocuments'
                        choose_file_btn_sitem = self.locator_finder_by_id(choose_file_btn)
                        choose_file_btn_sitem.send_keys(str(path1.absolute()))
                        time.sleep(1)

                    else:
                        raise Exception('neighbourhood Collection not found!')

                    self.navbar_goto("collections")
                    self.wait_for_ajax()
                    time.sleep(1)

                    # looking for restaurants collection has been created or not
                    restaurants_collection = "//*[text()='restaurants']"
                    restaurants_collection_sitem = self.locator_finder_by_xpath(
                        restaurants_collection
                    )
                    time.sleep(1)

                    if restaurants_collection_sitem.text == 'restaurants':
                        self.tprint('open it and populate necessary data into it \n')
                        restaurants_collection_sitem.click()
                        # selecting content submenu
                        content = "//div[@id='subNavigationBar']/ul[2]//a[.='Content']"
                        content_sitem = self.locator_finder_by_xpath(content)
                        content_sitem.click()
                        time.sleep(1)

                        self.tprint('select upload button \n')
                        upload = '//*[@id="importCollection"]/span/i'
                        self.locator_finder_by_xpath(upload).click()
                        time.sleep(1)

                        path2 = ui_data_dir / "ui_data" / "service_page" / "demo_geo_s2" / "neighborhoods.json"
                        self.tprint(f'Providing restaurants collection path {path2} \n')
                        choose_file_btn = 'importDocuments'
                        choose_file_btn_sitem = self.locator_finder_by_id(choose_file_btn)
                        choose_file_btn_sitem.send_keys(str(path2.absolute()))
                        time.sleep(1)

                        self.navbar_goto("services")
                        self.wait_for_ajax()
                        self.webdriver.refresh()

                        self.tprint('Selecting demo_geo_s2 service \n')
                        if self.version_is_newer_than("3.11.100"):
                            select_service = "(//a[@class='chakra-link css-yuehqk'])[1]"
                        else:
                            select_service = "//*[text()='demo-geo-s2']"

                        self.locator_finder_by_xpath(select_service).click()
                        time.sleep(1)

                        self.tprint('inspecting demo_geo_s2 service interface \n')
                        geo_service = '//*[@id="information"]/div/div[2]/div[2]/input'
                        self.locator_finder_by_xpath(geo_service).click()
                        time.sleep(4)

                        self.tprint('Switching interface tab \n')
                        self.webdriver.switch_to.window(self.webdriver.window_handles[1])

                        # inspecting from the service interface started here
                        self.wait_for_ajax()
                        self.tprint('Visualize random Restaurant \n')
                        random_restaurant = 'randomRestaurant'
                        self.locator_finder_by_id(random_restaurant).click()
                        time.sleep(3)

                        self.tprint('Visualize random Neighborhood \n')
                        random_neighborhood = 'randomNeighborhood'
                        self.locator_finder_by_id(random_neighborhood).click()
                        time.sleep(3)

                        self.tprint('Visualize Distance \n')
                        distance = 'geoDistance'
                        self.locator_finder_by_id(distance).click()
                        time.sleep(3)

                        self.tprint('Visualize Distance between \n')
                        distance_between = 'geoDistanceBetween'
                        self.locator_finder_by_id(distance_between).click()
                        time.sleep(3)

                        self.tprint('Visualize Geo distance nearest \n')
                        distance_nearest = 'geoDistanceNearest'
                        self.locator_finder_by_id(distance_nearest).click()
                        time.sleep(3)

                        self.tprint('Visualize Geo intersection \n')
                        intersection = 'geoIntersection'
                        self.locator_finder_by_id(intersection).click()
                        time.sleep(3)
                        self.tprint('Switching back to original window \n')
                        self.webdriver.close()
                        self.webdriver.switch_to.window(self.webdriver.window_handles[0])
                        self.wait_for_ajax()
                    else:
                        raise Exception('restaurants Collection not found!')

            except Exception as ex:
                raise Exception('Failed to create the service!!') from ex

    def check_demo_geo_s2_service_api(self):
        """Checking demo_geo_s2 service's API"""
        self.navbar_goto("services")
        self.wait_for_ajax()

        self.tprint('Selecting demo_geo_s2 service \n')
        if self.version_is_newer_than("3.11.100"):
            select_service = "(//a[@class='chakra-link css-yuehqk'])[1]"
        else:
            select_service = "//*[text()='demo-geo-s2']"

        self.locator_finder_by_xpath(select_service).click()
        time.sleep(1)

        self.tprint('Selecting service API \n')
        api = 'service-api'
        self.locator_finder_by_id(api).click()
        time.sleep(2)

        self.tprint("Changing view to JSON form \n")
        json = 'jsonLink'
        self.locator_finder_by_id(json).click()
        time.sleep(3)

        self.tprint('get back to swagger view \n')
        json = 'jsonLink'
        self.locator_finder_by_id(json).click()

    def checking_function_for_fox_leaflet(self, id_list):
        """this method will take list and check according to that list"""
        self.tprint(f'There are total {len(id_list)} Foxx leaflets \n')
        i = 0
        while i < len(id_list):
            self.tprint(f'Checking Foxx leaflet number {i}\n')
            self.locator_finder_by_xpath(id_list[i]).click()
            time.sleep(2)
            self.locator_finder_by_xpath(id_list[i]).click()

            i = i + 1
            if i == len(id_list):
                self.tprint('Checking Foxx leaflets finished \n')
            time.sleep(2)

    def inspect_demo_geo_foxx_leaflet_iframe(self):
        """Checking iframe elements of foxx and leaflets"""
        if self.version_is_newer_than("3.11.100"):
            self.tprint('skipped inspect_demo_geo_foxx_leaflet_iframe() \n')
        else:
            self.tprint("Switching to IFrame \n")
            iframe_id = "swaggerIframe"
            self.webdriver.switch_to.frame(self.locator_finder_by_id(iframe_id))
            time.sleep(1)

            self.tprint("Checking default view \n")
            default_view = "operations-tag-default"
            self.locator_finder_by_id(default_view).click()
            time.sleep(2)
            self.locator_finder_by_id(default_view).click()

            self.tprint("inspecting documentation through Foxx and leaflet \n")
            id_list = []
            if self.version_is_newer_than("3.10.0"):
                def template_str(leaflet):
                    return f"(//span[contains(text(),'{leaflet}')])[1]"
                id_list = [
                    template_str("/restaurants"),
                    template_str("/neighborhoods"),
                    template_str("/pointsInNeighborhood"),
                    template_str("/geoContainsBenchmark"),
                    template_str("/geoIntersection"),
                    template_str("/geoDistanceNearest"),
                    template_str("/geoDistanceBetween"),
                    template_str("/geoDistance"),
                    template_str("/geoDistanceBenchmark"),
                    template_str("/geoNearBenchmark"),
                ]

            self.checking_function_for_fox_leaflet(id_list)

            self.tprint("Getting out of IFrame \n")
            self.webdriver.switch_to.default_content()
            time.sleep(1)

    def inspect_foxx_leaflet_iframe(self):
        """Checking iframe elements of foxx and leaflets"""
        if self.version_is_newer_than("3.11.100"):
            self.tprint('skipped inspect_foxx_leaflet_iframe() \n')
        else:
            self.tprint('Switching to IFrame \n')
            iframe_id = 'swaggerIframe'
            self.webdriver.switch_to.frame(self.locator_finder_by_id(iframe_id))
            time.sleep(1)

            self.tprint("Checking default view \n")
            default_view = "operations-tag-default"
            self.locator_finder_by_id(default_view).click()
            time.sleep(2)
            self.locator_finder_by_id(default_view).click()

            self.tprint('inspecting documentation through Foxx and leaflet \n')
            id_list = []
            if self.version_is_newer_than("3.10.0"):
                def template_str(leaflet):
                    return f"(//span[contains(text(),'{leaflet}')])[1]"
                id_list = [
                    template_str("/restaurants"),
                    template_str("/neighborhoods"),
                    template_str("/pointsInNeighborhood"),
                    template_str("/geoContainsBenchmark"),
                    template_str("/geoIntersection"),
                    template_str("/geoDistanceNearest"),
                    template_str("/geoDistanceBetween"),
                    template_str("/geoDistance"),
                    template_str("/geoDistanceBenchmark"),
                    template_str("/geoNearBenchmark"),
                ]

            self.checking_function_for_fox_leaflet(id_list)

            self.tprint('Getting out of IFrame \n')
            self.webdriver.switch_to.default_content()
            time.sleep(1)

    def install_demo_graph_hql_service(self, mount_path):
        """Installing demo_graph_hql_service from the list"""
        self.navbar_goto("services")
        self.wait_for_ajax()
        self.select_add_service_button()
        self.tprint('Selecting graphql service \n')
        graphql = "//*[text()='demo-graphql']"
        graphql_sitem = self.locator_finder_by_xpath(graphql, benchmark=True)
        graphql_sitem.click()
        time.sleep(2)

        # ---------------checking graphql's links started here---------------

        # Fixme need to be fixed as github link removed from the website
        # self.tprint('Checking graphql Github link \n')
        # github_link = "//*[text()='graphql-sync wrapper for graphql-js']"
        # github_link_sitem = self.locator_finder_by_xpath(github_link)
        # page_title = super().switch_tab(github_link_sitem)

        # expected_title = 'GitHub - arangodb-foxx/demo-graphql: Example Foxx Service using GraphQL'

        # assert page_title == expected_title, f"Expected text {expected_title} but got {page_title}"

        # self.tprint('Checking graphql documentation link \n')
        # foxx_graphql_link = '//*[@id="readme"]/p[1]/a[2]'
        # foxx_graphql_link_sitem = self.locator_finder_by_xpath(foxx_graphql_link)
        # page_title = super().switch_tab(foxx_graphql_link_sitem)

        # expected_title = "Introduction to ArangoDB's Technical Documentation and Ecosystem | ArangoDB Documentation"

        # todo currently this is not working
        # assert page_title == expected_title, f"Expected text {expected_title} but got {page_title}"
        # ---------------checking graphql's links end here---------------

        self.tprint('Installing the graphql service started \n')
        install_graphql = 'installService'
        install_graphql_sitem = self.locator_finder_by_id(install_graphql, benchmark=True)
        install_graphql_sitem.click()
        time.sleep(3)

        self.tprint('Mounting the demo graphql service \n')
        mount_point = "/html//input[@id='new-app-mount']"
        mount_point_sitem = self.locator_finder_by_xpath(mount_point, benchmark=True)
        mount_point_sitem.click()
        mount_point_sitem.send_keys(mount_path)
        time.sleep(1)

        self.tprint('Install the service \n')
        install_btn = 'modalButton1'
        install_btn_sitem = self.locator_finder_by_id(install_btn, benchmark=True)
        install_btn_sitem.click()
        time.sleep(6)

        if self.version_is_newer_than("3.10.100"):
            # TODO
            self.tprint('skipped for now\n')
        else:
            self.webdriver.refresh()
            self.wait_for_ajax()
            self.navbar_goto("services")
            # at this point it will be back to service page
            max_retries = 3

            for attempt in range(1, max_retries + 1):
                try:
                    self.tprint('Selecting graphql service \n')
                    if self.version_is_newer_than("3.11.100"):
                        graphql_service = "(//a[normalize-space()='/graphql'])[1]"
                    else:
                        graphql_service = "//*[text()='/graphql']"

                    graphql_service_sitem = self.locator_finder_by_xpath(graphql_service)
                    graphql_service_sitem.click()
                    time.sleep(2)
                    status = True
                    break
                except NoSuchElementException as ex:
                    self.tprint(
                        f"Error occurred while selecting graphql service. Attempt {attempt} \n{ex}"
                    )

                    time.sleep(2)
                    self.tprint(f"Attempt {attempt}: Element not found. Retrying...")
                    if attempt == max_retries:
                        self.tprint("Maximum retries reached. Exiting.")
                        raise  ex # Re-raise the exception if max retries reached
                    status = False
                    self.tprint("Refreshing the UI \n")
                    self.webdriver.refresh()
                    time.sleep(2)
                    self.navbar_goto("services")
                    self.wait_for_ajax()
                    continue  # Retry the loop

            if status:
                self.tprint('Opening graphql interface \n')
                graphql_interface = '//*[@id="information"]/div/div[2]/div[2]/input'
                graphql_interface_sitem = self.locator_finder_by_xpath(graphql_interface)
                graphql_interface_sitem.click()

                self.tprint('Switching to code mirror windows of graphql \n')
                self.webdriver.switch_to.window(self.webdriver.window_handles[1])
                self.wait_for_ajax()
                graphql_interface_execute_btn = '//*[@id="graphiql-container"]/div[1]/div[1]/div/div[2]/button'
                graphql_interface_execute_btn_sitem = \
                    self.locator_finder_by_xpath(graphql_interface_execute_btn)
                graphql_interface_execute_btn_sitem.click()
                self.tprint('Return back to original window \n')
                self.webdriver.close() # closes the browser active window
                self.webdriver.switch_to.window(self.webdriver.window_handles[0])

                self.wait_for_ajax()
                self.tprint('Checking API tab of graphql service \n')
                graphql_api_name = 'service-api'
                graphql_api_sitem = self.locator_finder_by_id(graphql_api_name)
                graphql_api_sitem.click()
                time.sleep(1)

                if self.version_is_newer_than("3.10.100"):
                    self.tprint('skipped inspecting graphql service \n')
                else:
                    self.tprint('Selecting Swagger view \n')
                    swagger_view = 'jsonLink'
                    self.locator_finder_by_id(swagger_view).click()
                    time.sleep(2)
                    self.locator_finder_by_id(swagger_view).click()
                    time.sleep(2)

                    try:
                        if self.version_is_older_than("3.10.0"):

                            self.tprint('Switching to IFrame \n')
                            iframe_id = 'swaggerIframe'
                            self.webdriver.switch_to.frame(self.locator_finder_by_id(iframe_id))
                            time.sleep(1)

                            self.tprint("Checking default view \n")
                            default_view = "operations-tag-default"
                            self.locator_finder_by_id(default_view).click()
                            time.sleep(2)
                            self.locator_finder_by_id(default_view).click()

                            self.tprint('inspecting documentation through Foxx and leaflet \n')
                            first = '//*[@id="operations-default-get"]/div/button[1]/div'
                            second = '//*[@id="operations-default-post"]/div/button[1]/div'
                            id_list = [first, second]
                            self.checking_function_for_fox_leaflet(id_list)
                    except Exception as ex:
                        self.tprint(f"Error occurred while inspecting API tab of graphql service\n{ex}")
                        self.tprint('Getting out of IFrame \n')
                        self.webdriver.switch_to.default_content()
                        time.sleep(1)

    def replace_service(self):
        """This method will replace the service"""""
        self.navbar_goto("services")
        self.wait_for_ajax()

        if self.version_is_newer_than("3.11.100"):
            select_service = "(//a[@class='chakra-link css-yuehqk'])[1]"
            select_service_sitem = self.locator_finder_by_xpath(select_service)
            select_service_sitem.click()
        else:
            self.select_demo_geo_s2_service()

        self.select_service_settings()

        self.tprint("Replacing demo_geo_s2 service with demo-graphql service \n")
        replace_btn = "(//button[@class='app-replace upgrade button-warning'][normalize-space()='Replace'])[2]"
        self.locator_finder_by_xpath(replace_btn).click()
        time.sleep(1)

        new_service = "(//button[@appid='demo-graphql'])[1]"
        self.locator_finder_by_xpath(new_service).click()
        time.sleep(2)

        self.tprint("Run teardown before replacing service \n")
        tear_down = '//*[@id="new-app-flag-teardown"]'  # v3.9.1
        self.locator_finder_by_xpath(tear_down).click()
        time.sleep(1)

        self.tprint("discard configuration before replacing service \n")
        configuration = '//*[@id="new-app-flag-replace"]'  # v3.9.1
        self.locator_finder_by_xpath(configuration).click()
        time.sleep(1)

        self.tprint("replacing begins with graphql service \n")
        replace = "modalButton1"
        self.locator_finder_by_id(replace).click()
        time.sleep(3)

        if self.version_is_newer_than("3.11.100"):
            self.tprint('skipped handle_red_bar() \n')
        else:
            try:
                success_notification = super().handle_red_bar()
                time.sleep(2)
                # two pop-up msg comes very fast, hard to catch both of them, timing is key here.
                expected_msg_1 = "Services: Upgrading demo-graphql."
                expected_msg_2 = "Services: Service demo-graphql installed."
                assert (
                    success_notification in [expected_msg_1, expected_msg_2]
                ), f"Expected {expected_msg_1} or {expected_msg_2} but got {success_notification}"
            except Exception as ex:
                raise Exception("Error occurred!! required manual inspection.\n") from ex
            self.tprint("Service successfully replaced \n")

    def select_service_settings(self):
        """Selecting service settings tab"""
        self.tprint("Selecting settings options \n")
        settings = "service-settings"
        self.locator_finder_by_id(settings).click()

    def delete_service_from_setting_tab(self):
        """will remove a service"""
        delete_service = '//*[@id="settings"]/div/button[1]'
        self.locator_finder_by_xpath(delete_service).click()
        time.sleep(1)

        confirm_delete = 'modalButton1'
        self.locator_finder_by_id(confirm_delete).click()
        time.sleep(1)

        pressing_yes = 'modal-confirm-delete'
        self.locator_finder_by_id(pressing_yes).click()
        time.sleep(1)

        self.webdriver.refresh()

    def collection_deletion(self, col_id):
        """Collection will be deleted by this method"""
        if self.version_is_newer_than("3.11.100"):
            self.locator_finder_by_xpath(col_id).click()
        else:
            self.locator_finder_by_id(col_id).click()

        time.sleep(1)

        settings = "//*[text()='Settings']"
        self.locator_finder_by_xpath(settings).click()
        time.sleep(1)

        delete = "//*[text()='Delete']"
        self.locator_finder_by_xpath(delete).click()
        time.sleep(1)

        confirm_delete = '//*[@id="modal-confirm-delete"]'
        self.locator_finder_by_xpath(confirm_delete).click()
        time.sleep(1)

    def delete_service(self, service_name):
        """Delete all the services"""
        self.webdriver.refresh()
        self.navbar_goto("services")
        self.wait_for_ajax()

        if service_name == '/geo':

            try:
                # try to determine service has already been created
                service = "//*[text()='/geo']"
                service_sitem = self.locator_finder_by_xpath(service).text
                time.sleep(1)

                if service_sitem == '/geo':
                    self.tprint(f'{service_sitem} service has been found and ready to delete \n')
                    self.locator_finder_by_xpath(service).click()
                    time.sleep(1)
                    # move to settings tab
                    self.select_service_settings()
                    time.sleep(1)

                    self.delete_service_from_setting_tab()

                    self.webdriver.refresh()
                    self.tprint(f'{service_sitem} service has been deleted successfully \n')

            except TimeoutException:
                self.tprint('TimeoutException occurred! \n')
                self.tprint(f'Info: {service_name} has already been deleted or never created. \n')
            except Exception as ex:
                raise Exception('Critical Error occurred and need manual inspection!! \n') from ex

        if service_name == '/graphql':
            # try to determine service has already been created
            try:
                service = "//*[text()='/graphql']"
                service_sitem = self.locator_finder_by_xpath(service).text
                time.sleep(1)
                if service_sitem == '/graphql':
                    self.tprint(f'{service_sitem} service has been found and ready to delete \n')
                    self.locator_finder_by_xpath(service).click()
                    time.sleep(1)
                    # move to settings tab
                    self.select_service_settings()
                    time.sleep(1)

                    self.delete_service_from_setting_tab()
                    self.tprint(f'{service_sitem} service has been deleted successfully \n')
            except TimeoutException:
                self.tprint('TimeoutException occurred! \n')
                self.tprint(f'Info: {service_name} has already been deleted or never created. \n')
            except Exception as ex:
                raise Exception('Critical Error occurred and need manual inspection!! \n') from ex
