""" Operator integration tests general helper """

from random import randint
from time import sleep

RANGE_START = 10000
RANGE_END = 20000
SYNC_CHANGES_DELAY = 5


def generate_username(username="user"):
    random_suffix = str(randint(RANGE_START, RANGE_END))
    return f"{username}_{random_suffix}"


def delay_execution(delay=SYNC_CHANGES_DELAY):
    sleep(delay)
