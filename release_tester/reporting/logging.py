""" utils to use logs in allure report """
import collections
import io


class IoDuplicator(io.TextIOBase):
    """save text stream in memory and pass data to another stream"""

    def __init__(self, downstream, *args):
        self.downstream = downstream
        io.TextIOBase.__init__(self, *args)
        self.deque = collections.deque()

    def getvalue(self):
        """return saved text data"""
        return "".join(self.deque)

    def write(self, x):
        self.downstream.write(x)
        self.downstream.flush()
        self.deque.append(x)
