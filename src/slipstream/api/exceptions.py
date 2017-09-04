"""
Exceptions.
"""


class SlipStreamError(Exception):
    def __init__(self, reason, response=None):
        super(SlipStreamError, self).__init__(reason)
        self.reason = reason
        self.response = response
