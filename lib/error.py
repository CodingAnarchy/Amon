import logging

logger = logging.getLogger(__name__)


class LoginError(Exception):
    def __init__(self, msg):
        logger.error(msg)
        self.msg = msg
        pass


class KeybaseError(Exception):
    def __init__(self, msg):
        logger.error(msg)
        self.msg = msg
        pass


class CSRFError(Exception):
    def __init__(self, stored, ret):
        self.msg = "CSRF mismatch occurred!\nStored CSRF: " + stored + "\nReturned CSRF: " + ret
        logger.error(self.msg)

    def __str__(self):
        return self.msg


class CSRFWarning(Warning):
    def __init__(self, msg):
        logger.error(msg)
        self.msg = msg
        pass
