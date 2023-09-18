

class TestConfig:
    """this represents one tests configuration"""

    # pylint: disable=too-many-instance-attributes disable=too-few-public-methods
    def __init__(self):
        self.phase = "jam"
        self.parallelity = 3
        self.db_count = 100
        self.db_count_chunks = 5
        self.min_replication_factor = 2
        self.max_replication_factor = 3
        self.data_multiplier = 4
        self.collection_multiplier = 1
        self.launch_delay = 1.3
        self.single_shard = False
        self.db_offset = 0
        self.progressive_timeout = 10000
        self.hot_backup = False
        self.bench_jobs = []
        self.arangosh_jobs = []
        self.dump_jobs = []
        self.restore_jobs = []
        self.system_makedata = False
        self.makedata_args = []
