import collections
import io

from allure_commons._allure import attach


class AllureLogInterceptor(io.TextIOBase):
    def __init__(self, size=100 * 1024**2, *args):
        self.maxsize = size
        io.TextIOBase.__init__(self, *args)
        self.deque = collections.deque()

    def getvalue(self):
        return ''.join(self.deque)

    def write(self, x):
        self.deque.append(x)
        self.shrink()

    def shrink(self):
        if self.maxsize is None:
            return
        size = sum(len(x) for x in self.deque)
        while size > self.maxsize:
            x = self.deque.popleft()
            size -= len(x)

    def save_logs(self):
        attach(self.getvalue(), "Log output")
        self.deque.clear()


class IoDuplicator(io.TextIOBase):
    def __init__(self, downstream, *args):
        self.downstream = downstream
        io.TextIOBase.__init__(self, *args)
        self.deque = collections.deque()

    def getvalue(self):
        return ''.join(self.deque)

    def write(self, x):
        self.downstream.write(x)
        self.deque.append(x)