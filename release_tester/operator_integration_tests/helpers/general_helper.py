""" Operator integration tests general helper """

import json

from random import randint
from time import sleep

RANGE_START = 10000
RANGE_END = 20000
SYNC_CHANGES_DELAY = 5
TEST_DATA_PARAM = "$1"


def generate_username(username="user"):
    random_suffix = str(randint(RANGE_START, RANGE_END))
    return f"{username}_{random_suffix}"


def delay_execution(delay=SYNC_CHANGES_DELAY):
    sleep(delay)


def update_test_data(test_data, test_data_param=""):
    test_data_str = json.dumps(test_data)
    test_data_str = test_data_str.replace(TEST_DATA_PARAM, test_data_param)
    return json.loads(test_data_str)
