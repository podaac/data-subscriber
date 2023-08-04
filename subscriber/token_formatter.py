import logging
import re


class TokenFormatter(logging.Formatter):
    """Formatter that removes sensitive information in urls."""
    @staticmethod
    def _filter(s):

        return re.sub(r'token=(.*)\??', r'token=****', s)

    def format(self, record):
        original = logging.Formatter.format(self, record)
        return self._filter(original)
