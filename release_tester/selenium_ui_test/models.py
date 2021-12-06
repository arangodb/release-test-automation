#!/usr/bin/env python3
"""abstract base models"""
from enum import Enum

# pylint: disable=too-few-public-methods

class IndexType(Enum):
    """which type of index"""

    PERSISTENT = "Persistent"
    GEO = "Geo"
    FULLTEXT = "Fulltext"
    TTL = "Ttl"


class RtaUiTestResult:
    """abstract a ui result"""
    def __init__(self, name, success, message, traceback):
        self.name = name
        self.success = success
        self.message = message
        self.traceback = traceback
