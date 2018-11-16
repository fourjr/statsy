import logging
import requests
import os


class LoggingHandler(logging.Handler):
    def __init__(self, log_level):
        super().__init__(log_level)
        super().setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

    def emit(self, record):
        print(record)
        log_entry = self.format(record)
        print(log_entry)
        return requests.post(os.getenv('log_hook'), log_entry).content
