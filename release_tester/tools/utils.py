#!/usr/bin/env python3
import re
import semver

COLUMN_CACHE_ARGUMENT = "--args.all.arangosearch.columns-cache-limit=500000"

def extract_version(version_str):
    match = re.match(r"\w+\[(.+)\]", version_str)
    if match:
        # upgrade
        version_str = match[1]
    return version_str

        
def is_column_cache_supported(version_str):
    version = extract_version(version_str)
    return semver.compare(version, "3.9.5") == 0 or semver.compare(version, "3.10.2") >= 0