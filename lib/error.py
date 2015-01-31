class LoginError(Exception):
    pass


class KeybaseError(Exception):
    pass


class CSRFError(Exception):
    def __init__(self, stored, ret):
        self.msg = "CSRF mismatch occurred!\nStored CSRF: " + stored + "\nReturned CSRF: " + ret

    def __str__(self):
        return self.msg


class CSRFWarning(Warning):
    pass
