#!/usr/bin/env python3
"""abstract base models"""
from enum import Enum


class IndexType(Enum):
    """which type of index"""

    PERSISTENT = "Persistent"
    GEO = "Geo"
    FULLTEXT = "Fulltext"
    TTL = "Ttl"


class RtaUiTestResult:
    """abstract a ui result"""

    def __init__(self, name, success, message, tb):
        self.name = name
        self.success = success
        self.message = message
        self.tb = tb
