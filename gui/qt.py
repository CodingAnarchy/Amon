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

        self.initUI()

    def initUI(self):
        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(QtGui.qApp.quit)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

        self.statusBar().showMessage('Ready')
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('Amon ' + AMON_VERSION)
        self.show()


def main():
    app = QtGui.QApplication(sys.argv)
    amon = Amon()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
