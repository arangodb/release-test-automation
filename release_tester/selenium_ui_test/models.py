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
