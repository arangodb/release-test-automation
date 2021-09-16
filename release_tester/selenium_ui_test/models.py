from enum import Enum


class IndexType(Enum):
    PERSISTENT = "Persistent"
    GEO = "Geo"
    FULLTEXT = "Fulltext"
    TTL = "Ttl"


class RtaUiTestResult():
    def __init__(self, name, success, message, tb):
        self.name = name
        self.success = success
        self.message = message
        self.tb = tb