""" utils to use logs in allure report """

import collections
import io


# This class is intended to save everything that is being written to stdout/stderr
# in memory to later add it to the allure report. The text data is stored in a 2-dimensional collection.
# Each time a new allure step is initialized, new collection is created. When new step us started,
# `grow_stack` method must be called. When step is finished, `pop_stack` must be called.
# `pop_stack` returns text written to the downstream during step execution as a single string to be saved in the report.
# Steps are expected to finish in the reverse order of when they are started.
# pylint: disable=missing-class-docstring disable=missing-function-docstring
class IoDuplicator(io.TextIOBase):

    def __init__(self, downstream, *args):
        self.downstream = downstream
        io.TextIOBase.__init__(self, *args)
        self.deque = collections.deque()

    def grow_stack(self):
        self.deque.append(collections.deque())

    def pop_stack(self):
        top_deque = self.deque.pop()
        return "".join(top_deque)

    def write(self, x):
        line = self.downstream.write(
            x,
        )
        self.downstream.flush()
        if len(self.deque) > 0:
            self.deque[-1].append(x)
        return line
