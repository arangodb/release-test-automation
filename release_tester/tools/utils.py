#!/usr/bin/env python3
import re
import semver

# 402_views.js expects this limit to be 5000. If this value is changed, it must be changed here, in 402_views.js
# and also in js/client/modules/arangodb/testsuites/rta_makedata.js(in the arangodb repo)
ARANGOSEARCH_COLUMNS_CACHE_LIMIT = 5000
COLUMN_CACHE_ARGUMENT = f"--args.all.arangosearch.columns-cache-limit={ARANGOSEARCH_COLUMNS_CACHE_LIMIT}"

def extract_version(version_str):
    match = re.match(r"\w+\[(.+)\]", version_str)
    if match:
        # upgrade
        version_str = match[1]
    return version_str

        
def is_column_cache_supported(version_str):
    version = extract_version(version_str)
    return semver.compare(version, "3.9.5") >= 0 and semver.compare(version, "3.10.0") != 0 and semver.compare(version, "3.10.1") != 0
