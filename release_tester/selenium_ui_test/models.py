from enum import Enum


class IndexType(Enum):
    PERSISTENT = "Persistent"
    GEO = "Geo"
    FULLTEXT = "Fulltext"
    TTL = "Ttl"