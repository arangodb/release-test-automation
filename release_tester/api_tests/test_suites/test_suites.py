from api_tests.test_suites.vi_stored_values_suite import VectorIndexStoredValuesTestSuite
from api_tests.test_suites.versioned_api_suite import VersionedAPITestSuite


class TestSuites:
    """This class contains all API test suites"""

    test_suites = [VectorIndexStoredValuesTestSuite, VersionedAPITestSuite]
