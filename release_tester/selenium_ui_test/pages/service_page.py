#!/usr/bin/env python3
""" service page object """
import time
import semver
from selenium.common.exceptions import TimeoutException
from selenium_ui_test.pages.navbar import NavigationBarPage


class ServicePage(NavigationBarPage):
    """service page object"""
    # pylint: disable=too-many-instance-attributes
    def __init__(self, driver, cfg):
        super().__init__(driver, cfg)
        self.service_page = 'services'

    def select_service_page(self):
        """Selecting service page"""
        service = self.service_page
        service_sitem = self.locator_finder_by_id(service)
        service_sitem.click()
        time.sleep(2)

    def select_add_service_button(self):
        """selecting new service button"""
        add_new_service = 'addApp'
        add_new_service_stiem = self.locator_finder_by_id(add_new_service)
        add_new_service_stiem.click()
        time.sleep(2)

    def service_search_option(self, search_keyword):
        """checking service page search options"""
        search = 'foxxSearch'
        service_search_stiem = self.locator_finder_by_id(search)
        service_search_stiem.click()
        service_search_stiem.clear()
        time.sleep(2)

        print(f'Searching for {search_keyword} \n')
        service_search_stiem.send_keys(search_keyword)
        time.sleep(1)

        # checking search find the correct demo services
        if search_keyword == 'demo':
            search_item = "//*[text()='demo-graphql']"
            expected_text = 'demo-graphql'
            demo_graphql_stiem = self.locator_finder_by_xpath(search_item)
            # print(f'{demo_graphql_stiem}')
            assert demo_graphql_stiem.text == expected_text, f"Expected text {expected_text} " \
                                                             f"but got {demo_graphql_stiem.text}"
        if search_keyword == 'tab':
            search_item = "//*[text()='tableau-connector']"
            expected_text = 'tableau-connector'
            demo_graphql_stiem = self.locator_finder_by_xpath(search_item)
            # print(f'{demo_graphql_stiem}')
            assert demo_graphql_stiem.text == expected_text, f"Expected text {expected_text} " \
                                                             f"but got {demo_graphql_stiem.text}"
        if search_keyword == 'grafana':
            search_item = "//*[text()='grafana-connector']"
            expected_text = 'grafana-connector'
            demo_graphql_stiem = self.locator_finder_by_xpath(search_item)
            assert demo_graphql_stiem.text == expected_text, f"Expected text {expected_text} " \
                                                             f"but got {demo_graphql_stiem.text}"

    def service_category_option(self):
        """checking service page category options"""
        category = 'categorySelection'

        print('Selecting category options \n')
        select_service_category_sitem = self.locator_finder_by_id(category)
        select_service_category_sitem.click()
        time.sleep(1)

    def service_filter_category_option(self):
        """selecting category search option"""
        filter_option = 'Category-filter'
        filter_option_stiem = self.locator_finder_by_xpath(filter_option)
        filter_option_stiem.click()
        filter_option_stiem.clear()
        time.sleep(1)

    def select_category_option_from_list(self, category):
        """checking service page category options"""
        if category == 'connector':
            print(f'Selecting {category} category from the drop-down menu \n')
            connector_name = '//*[@id="connector-option"]/span[3]'
            connector_stiem = self.locator_finder_by_xpath(connector_name)
            connector_stiem.click()
            time.sleep(1)
            connector_stiem.click()

        if category == 'service':
            print(f'Selecting {category} category from the drop-down menu \n')
            connector_name = '//*[@id="service-option"]/span[3]'
            connector_stiem = self.locator_finder_by_xpath(connector_name)
            connector_stiem.click()
            time.sleep(1)
            connector_stiem.click()

        if category == 'geo':
            print(f'Selecting {category} category from the drop-down menu \n')
            connector_name = '//*[@id="geo-option"]/span[3]'
            connector_stiem = self.locator_finder_by_xpath(connector_name)
            connector_stiem.click()
            time.sleep(1)
            connector_stiem.click()

        if category == 'demo':
            print(f'Selecting {category} category from the drop-down menu \n')
            connector_name = '//*[@id="demo-option"]/span[3]'
            connector_stiem = self.locator_finder_by_xpath(connector_name)
            connector_stiem.click()
            time.sleep(1)
            connector_stiem.click()

        if category == 'graphql':
            print(f'Selecting {category} category from the drop-down menu \n')
            connector_name = '//*[@id="graphql-option"]/span[3]'
            connector_stiem = self.locator_finder_by_xpath(connector_name)
            connector_stiem.click()
            time.sleep(1)
            connector_stiem.click()

        if category == 'prometheus':
            print(f'Selecting {category} category from the drop-down menu \n')
            connector_name = '//*[@id="prometheus-option"]/span[3]'
            connector_stiem = self.locator_finder_by_xpath(connector_name)
            connector_stiem.click()
            time.sleep(1)
            connector_stiem.click()

        if category == 'monitoring':
            print(f'Selecting {category} category from the drop-down menu \n')
            connector_name = '//*[@id="monitoring-option"]/span[3]'
            connector_stiem = self.locator_finder_by_xpath(connector_name)
            connector_stiem.click()
            time.sleep(1)
            connector_stiem.click()

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

    def select_demo_geo_s2_service(self):
        """Selecting demo geo s2 service from the list"""
        self.webdriver.refresh()
        print('Selecting demo_geo_s2 service \n')
        geo_service = "//*[text()='demo-geo-s2']"
        geo_service_sitem = self.locator_finder_by_xpath(geo_service)
        geo_service_sitem.click()
        time.sleep(2)

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

    def install_demo_geo_s2_service(self, mount_path, test_data_dir):
        """Installing demo geo s2 service from the list"""
        self.select_demo_geo_s2_service()

        print('Installing demo_geo_s2 service \n')
        service = 'installService'
        service_sitem = self.locator_finder_by_id(service)
        service_sitem.click()
        time.sleep(2)

        print(f'Selecting service mount point at {mount_path} \n')
        mount_point = 'new-app-mount'
        mount_point_sitem = self.locator_finder_by_id(mount_point)
        mount_point_sitem.click()
        mount_point_sitem.clear()
        mount_point_sitem.send_keys(mount_path)

        # selecting install button
        print('Selecting install button \n')
        install_btn = 'modalButton1'
        install_btn_sitem = self.locator_finder_by_id(install_btn)
        install_btn_sitem.click()
        time.sleep(6)

        # checking service has been created successfully
        # success = '//*[@id="installedList"]/div[2]/div/div[1]/p[2]/span'
        # success = '//*[@id="installedList"]/div[6]/div/div[1]/p[2]/span'
        success = "//*[text()='demo-geo-s2']"

        try:
            success_sitem = self.locator_finder_by_xpath(success).text
            if success_sitem == 'demo-geo-s2':
                print(f"{success_sitem} has been successfully created \n")
                status = True
            else:
                print('Could not locate the desired service! refreshing the UI \n')
                self.webdriver.refresh()
                time.sleep(1)
                success_sitem = self.locator_finder_by_xpath(success).text
                if success_sitem == 'demo-geo-s2':
                    print(f"{success_sitem} has been successfully created \n")
                    status = True
                else:
                    status = False
                time.sleep(2)

            # populating collections with necessary data
            if status:
                # got to collection tab
                self.navbar_goto("collections")
                self.webdriver.refresh()
                time.sleep(2)

                # looking for default collection has been created or not
                neighbourhood_collection = '//*[@id="collection_neighborhoods"]/div/h5'
                neighbourhoods_collection_sitem = self.locator_finder_by_xpath(neighbourhood_collection)

                if neighbourhoods_collection_sitem.text == 'neighborhoods':
                    print('open it and populate necessary data into it \n')
                    neighbourhoods_collection_sitem.click()
                    print('select upload button \n')
                    upload = '//*[@id="importCollection"]/span/i'
                    self.locator_finder_by_xpath(upload).click()
                    time.sleep(1)

                    path1 = test_data_dir / "ui_data" / "service_page" / "demo_geo_s2" / "neighborhoods.json"
                    print(f'Providing neighborhood collection path {path1} \n')
                    choose_file_btn = 'importDocuments'
                    choose_file_btn_sitem = self.locator_finder_by_id(choose_file_btn)
                    choose_file_btn_sitem.send_keys(str(path1.absolute()))
                    time.sleep(1)

                    print('Pressing on confirm btn \n')
                    confirm_btn = 'confirmDocImport'
                    self.locator_finder_by_id(confirm_btn).click()
                    time.sleep(1)
                    # going back to collection tab
                    self.webdriver.back()

                else:
                    raise Exception('neighbourhood Collection not found!')

                # looking for restaurants collection has been created or not
                restaurants_collection = '//*[@id="collection_restaurants"]/div/h5'
                restaurants_collection_sitem = self.locator_finder_by_xpath(restaurants_collection)
                time.sleep(1)

                if restaurants_collection_sitem.text == 'restaurants':
                    print('open it and populate necessary data into it \n')
                    restaurants_collection_sitem.click()
                    print('select upload button \n')
                    upload = '//*[@id="importCollection"]/span/i'
                    self.locator_finder_by_xpath(upload).click()
                    time.sleep(1)

                    path2 = test_data_dir / "ui_data" / "service_page" / "demo_geo_s2" / "neighborhoods.json"
                    print(f'Providing restaurants collection path {path2} \n')
                    choose_file_btn = 'importDocuments'
                    choose_file_btn_sitem = self.locator_finder_by_id(choose_file_btn)
                    choose_file_btn_sitem.send_keys(str(path2.absolute()))
                    time.sleep(1)

                    print('Pressing on confirm btn \n')
                    confirm_btn = 'confirmDocImport'
                    self.locator_finder_by_id(confirm_btn).click()
                    time.sleep(1)

                    self.select_service_page()
                    self.webdriver.refresh()

                    print('Selecting demo_geo_s2 service \n')
                    select_service = "//*[text()='demo-geo-s2']"
                    self.locator_finder_by_xpath(select_service).click()
                    time.sleep(1)

                    print('inspecting demo_geo_s2 service interface \n')
                    geo_service = '//*[@id="information"]/div/div[2]/div[2]/input'
                    self.locator_finder_by_xpath(geo_service).click()
                    time.sleep(4)

                    print('Switching interface tab \n')
                    self.webdriver.switch_to.window(self.webdriver.window_handles[1])

                    # inspecting from the service interface started here
                    print('Visualize random Restaurant \n')
                    random_restaurant = 'randomRestaurant'
                    self.locator_finder_by_id(random_restaurant).click()
                    time.sleep(3)

                    print('Visualize random Neighborhood \n')
                    random_neighborhood = 'randomNeighborhood'
                    self.locator_finder_by_id(random_neighborhood).click()
                    time.sleep(3)

                    print('Visualize Distance \n')
                    distance = 'geoDistance'
                    self.locator_finder_by_id(distance).click()
                    time.sleep(3)

                    print('Visualize Distance between \n')
                    distance_between = 'geoDistanceBetween'
                    self.locator_finder_by_id(distance_between).click()
                    time.sleep(3)

                    print('Visualize Geo distance nearest \n')
                    distance_nearest = 'geoDistanceNearest'
                    self.locator_finder_by_id(distance_nearest).click()
                    time.sleep(3)

                    print('Visualize Geo intersection \n')
                    intersection = 'geoIntersection'
                    self.locator_finder_by_id(intersection).click()
                    time.sleep(3)
                    self.webdriver.close() # closes the browser active window
                    print('Switching back to original window \n')
                    self.webdriver.close()
                    self.webdriver.switch_to.window(self.webdriver.window_handles[0])

                else:
                    raise Exception('restaurants Collection not found!')

        except Exception as ex:
            raise Exception('Failed to create the service!!') from ex

    def check_demo_geo_s2_service_api(self):
        """Checking demo_geo_s2 service's API"""
        self.select_service_page()

        print('Selecting demo_geo_s2 service \n')
        select_service = "//*[text()='demo-geo-s2']"
        self.locator_finder_by_xpath(select_service).click()
        time.sleep(1)

        print('Selecting service API \n')
        api = 'service-api'
        self.locator_finder_by_id(api).click()
        time.sleep(2)

        print("Changing view to JSON form \n")
        json = 'jsonLink'
        self.locator_finder_by_id(json).click()
        time.sleep(3)

        print('get back to swagger view \n')
        json = 'jsonLink'
        self.locator_finder_by_id(json).click()

    def checking_function_for_fox_leaflet(self, id_list):
        """this method will take list and check according to that list"""
        print(f'There are total {len(id_list)} Foxx leaflets \n')
        i = 0
        while i < len(id_list):
            print(f'Checking Foxx leaflet number {i}\n')
            self.locator_finder_by_xpath(id_list[i]).click()
            time.sleep(2)
            self.locator_finder_by_xpath(id_list[i]).click()

            i = i + 1
            if i == len(id_list):
                print('Checking Foxx leaflets finished \n')
            time.sleep(2)

    def inspect_foxx_leaflet_iframe(self):
        """Checking iframe elements of foxx and leaflets"""
        print('Switching to IFrame \n')
        iframe_id = 'swaggerIframe'
        self.webdriver.switch_to.frame(self.locator_finder_by_id(iframe_id))
        time.sleep(1)

        print("Checking default view \n")
        default_view = "operations-tag-default"
        self.locator_finder_by_id(default_view).click()
        time.sleep(2)
        self.locator_finder_by_id(default_view).click()

        print('inspecting documentation through Foxx and leaflet \n')
        template_str = lambda leaflet: f'//*[@id="operations-default-GET_{leaflet}"]/div/span[1]'

        id_list = [template_str('restaurants'),
                   template_str('neighborhoods'),
                   template_str('pointsInNeighborhood_id'),
                   template_str('geoContainsBenchmark_count'),
                   template_str('geoIntersection'),
                   template_str('geoDistanceNearest'),
                   template_str('geoDistanceBetween'),
                   template_str('geoDistance'),
                   template_str('geoDistanceBenchmark_count'),
                   template_str('geoNearBenchmark_count')]

        self.checking_function_for_fox_leaflet(id_list)

        print('Getting out of IFrame \n')
        self.webdriver.switch_to.default_content()
        time.sleep(1)

    def install_demo_graph_hql_service(self, mount_path):
        """Installing demo_graph_hql_service from the list"""
        self.select_service_page()
        self.select_add_service_button()

        print('Selecting graphql service \n')
        graphql = "//*[text()='demo-graphql']"
        graphql_sitem = self.locator_finder_by_xpath(graphql)
        graphql_sitem.click()
        time.sleep(2)

        # ---------------checking graphql's links started here---------------

        # Fixme need to be fixed as github link removed from the website
        # print('Checking graphql Github link \n')
        # github_link = "//*[text()='graphql-sync wrapper for graphql-js']"
        # github_link_sitem = self.locator_finder_by_xpath(github_link)
        # page_title = super().switch_tab(github_link_sitem)

        # expected_title = 'GitHub - arangodb-foxx/demo-graphql: Example Foxx Service using GraphQL'

        # assert page_title == expected_title, f"Expected text {expected_title} but got {page_title}"

        print('Checking graphql documentation link \n')
        foxx_graphql_link = '//*[@id="readme"]/p[1]/a[2]'
        foxx_graphql_link_sitem = self.locator_finder_by_xpath(foxx_graphql_link)
        page_title = super().switch_tab(foxx_graphql_link_sitem)

        expected_title = "Introduction to ArangoDB's Technical Documentation and Ecosystem | ArangoDB Documentation"

        assert page_title == expected_title, f"Expected text {expected_title} but got {page_title}"
        # ---------------checking graphql's links end here---------------

        print('Installing the graphql service started \n')
        install_graphql = 'installService'
        install_graphql_sitem = self.locator_finder_by_id(install_graphql)
        install_graphql_sitem.click()
        time.sleep(3)

        print('Mounting the demo graphql service \n')
        mount_point = 'new-app-mount'
        mount_point_sitem = self.locator_finder_by_id(mount_point)
        mount_point_sitem.click()
        mount_point_sitem.send_keys(mount_path)
        time.sleep(1)

        print('Install the service \n')
        install_btn = 'modalButton1'
        install_btn_sitem = self.locator_finder_by_id(install_btn)
        install_btn_sitem.click()
        time.sleep(2)
        self.webdriver.refresh()
        self.navbar_goto("services")

        # at this point it will be back to service page
        print('Selecting graphql service \n')
        graphql_service = "//*[text()='demo-graphql']"
        graphql_service_sitem = self.locator_finder_by_xpath(graphql_service)
        graphql_service_sitem.click()
        time.sleep(2)

        print('Opening graphql interface \n')
        graphql_interface = '//*[@id="information"]/div/div[2]/div[2]/input'
        graphql_interface_stiem = self.locator_finder_by_xpath(graphql_interface)
        graphql_interface_stiem.click()

        print('Switching to code mirror windows of graphql \n')
        self.webdriver.switch_to.window(self.webdriver.window_handles[1])

        graphql_interface_execute_btn = '//*[@id="graphiql-container"]/div[1]/div[1]/div/div[2]/button'
        graphql_interface_execute_btn_sitem = \
            self.locator_finder_by_xpath(graphql_interface_execute_btn)
        graphql_interface_execute_btn_sitem.click()
        print('Return back to original window \n')
        self.webdriver.close() # closes the browser active window
        self.webdriver.switch_to.window(self.webdriver.window_handles[0])

        print('Checking API tab of graphql service \n')
        graphql_api_name = 'service-api'
        graphql_api_sitem = self.locator_finder_by_id(graphql_api_name)
        graphql_api_sitem.click()
        time.sleep(1)

        print('Selecting Swagger view \n')
        swagger_view = 'jsonLink'
        self.locator_finder_by_id(swagger_view).click()
        time.sleep(2)
        self.locator_finder_by_id(swagger_view).click()
        time.sleep(2)

        print('Switching to IFrame \n')
        iframe_id = 'swaggerIframe'
        self.webdriver.switch_to.frame(self.locator_finder_by_id(iframe_id))
        time.sleep(1)

        print("Checking default view \n")
        default_view = "operations-tag-default"
        self.locator_finder_by_id(default_view).click()
        time.sleep(2)
        self.locator_finder_by_id(default_view).click()

        print('inspecting documentation through Foxx and leaflet \n')
        first = '//*[@id="operations-default-get"]/div/span[1]'
        second = '//*[@id="operations-default-post"]/div/span[1]'

        id_list = [first, second]
        self.checking_function_for_fox_leaflet(id_list)

        print('Getting out of IFrame \n')
        self.webdriver.switch_to.default_content()
        time.sleep(1)

    def replace_service(self):
        """This method will replace the service"""""
        self.select_service_page()
        self.select_demo_geo_s2_service()
        self.select_service_settings()

        print('Replacing demo_geo_s2 service with demo-graphql service \n')
        replace_btn = "(//button[@class='app-replace upgrade button-warning'][normalize-space()='Replace'])[2]"
        self.locator_finder_by_xpath(replace_btn).click()
        time.sleep(1)

        new_service = "(//button[@appid='demo-graphql'])[1]"
        self.locator_finder_by_xpath(new_service).click()
        time.sleep(2)

        print("Run teardown before replacing service \n")

        if self.current_package_version() >= semver.VersionInfo.parse("3.9.0"):
            tear_down = '//*[@id="new-app-flag-teardown"]' 
            configuration = '//*[@id="new-app-flag-replace"]'
        else:
            tear_down = "(//input[@value='false'])[1]"    
            configuration = "(//input[@value='false'])[2]"

        self.locator_finder_by_xpath(tear_down).click()
        time.sleep(1)

        print("discard configuration before replacing service \n")
        self.locator_finder_by_xpath(configuration).click()
        time.sleep(1)

        print("replacing begins with graphql service \n")
        replace = 'modalButton1'
        self.locator_finder_by_id(replace).click()
        time.sleep(3)
        try:
            success_notification = self.handle_red_bar()
            time.sleep(2)
            expected_msg = 'Services: Service demo-graphql installed.'
            assert expected_msg == success_notification, f"Expected {expected_msg} but got {success_notification}"
        except Exception as ex:
            raise Exception('Error occurred!! required manual inspection.\n'
                            ) from ex
        print('Service successfully replaced \n')

    def select_service_settings(self):
        """Selecting service settings tab"""
        print('Selecting settings options \n')
        settings = 'service-settings'
        self.locator_finder_by_id(settings).click()\

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
        print(f'Deleting {col_id} collections \n')
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
        print(f'Deleting {col_id} collections completed \n')
        time.sleep(1)

    def delete_service(self, service_name):
        """Delete all the services"""
        self.select_service_page()

        if service_name == '/geo':

            try:
                # try to determine service has already been created
                service = "//*[text()='/geo']"
                service_sitem = self.locator_finder_by_xpath(service).text
                time.sleep(1)

                if service_sitem == '/geo':
                    print(f'{service_sitem} service has been found and ready to delete \n')
                    self.locator_finder_by_xpath(service).click()
                    time.sleep(1)
                    # move to settings tab
                    self.select_service_settings()
                    time.sleep(1)

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
                    print(f'{service_sitem} service has been deleted successfully \n')

                    self.navbar_goto("collections")
                    # deleting neighborhood collection
                    self.collection_deletion('collection_neighborhoods')
                    self.collection_deletion('collection_restaurants')
            except TimeoutException:
                print('TimeoutException occurred! \n')
                print(f'Info: {service_name} has already been deleted or never created. \n')
            except Exception:
                raise Exception('Critical Error occurred and need manual inspection!! \n')

        if service_name == '/graphql':
            # try to determine service has already been created
            try:
                service = "//*[text()='/graphql']"
                service_sitem = self.locator_finder_by_xpath(service).text
                time.sleep(1)
                if service_sitem == '/graphql':
                    print(f'{service_sitem} service has been found and ready to delete \n')
                    self.locator_finder_by_xpath(service).click()
                    time.sleep(1)
                    # move to settings tab
                    self.select_service_settings()
                    time.sleep(1)

                    self.delete_service_from_setting_tab()
                    print(f'{service_sitem} service has been deleted successfully \n')

            except TimeoutException:
                print('TimeoutException occurred! \n')
                print(f'Info: {service_name} has already been deleted or never created. \n')
            except Exception:
                raise Exception('Critical Error occurred and need manual inspection!! \n')
