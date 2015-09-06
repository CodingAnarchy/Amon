from lib.version import AMON_VERSION
from lib.keybase import KeybaseUser
from lib.gmail import GmailUser
from lib.addresses import AddressBook
import lib.gpg as gpg

import sys
import logging
import json
from PyQt4 import QtGui


class Amon(QtGui.QMainWindow):
    def __init__(self):
        super(Amon, self).__init__()
        self.keybase_user = KeybaseUser()
        self.gmail = GmailUser()
        self.address_book = AddressBook()
