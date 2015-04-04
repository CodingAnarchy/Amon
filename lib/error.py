import logging

logger = logging.getLogger(__name__)


class AddressBookError(Exception):
    def __init__(self, msg):
        logger.error(msg)
        self.msg = msg


class CSRFError(Exception):
    def __init__(self, stored, ret):
        self.msg = "CSRF mismatch occurred!\nStored CSRF: " + stored + "\nReturned CSRF: " + ret
        logger.error(self.msg)


class LoginError(Exception):
    def __init__(self, msg):
        logger.error(msg)
        self.msg = msg


class KeybaseError(Exception):
    def __init__(self, msg):
        logger.error(msg)
        self.msg = msg


class CSRFWarning(RuntimeWarning):
    def __init__(self, msg):
        logger.error(msg)
        self.msg = msg
