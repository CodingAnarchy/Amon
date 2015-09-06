from lib.version import AMON_VERSION
from lib.keybase import KeybaseUser
from lib.gmail import GmailUser
from lib.addresses import AddressBook
from lib.utils import zero_out
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
        self.config = {}
        self.init_config()

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
        self.init_mailbox_view()
        self.show()

    def init_mailbox_view(self):
        mailbox_view = QtGui.QTreeView()

        mailbox_tree = QtGui.QTreeWidget()
        mailbox_tree.setColumnCount(2)
        mailbox_tree.setHeaderLabels(['Mailbox', 'Unread'])

        print self.gmail.get_mailbox_list(unread=True)

    def init_config(self):
        passphrase = ""
        try:
            with open('amon.conf', 'r') as f:
                passphrase = self.passphrase_dialog()
                data = gpg.decrypt_msg(f.read(), passphrase)
                self.config = json.loads(data)
                # zero_out(passphrase)
        except IOError:
            with open('../test.conf', 'r') as f:
                data = f.read()
                self.config = json.loads(data)

        if not self.config['keybase_user'] == '' and not self.config['keybase_pw'] == '':
            self.keybase_user.login(self.config['keybase_user'], self.config['keybase_pw'])

        if not self.config['email_addr'] == '' and not self.config['email_pw'] == '':
            self.gmail.login(self.config['email_addr'], self.config['email_pw'])

    def passphrase_dialog(self):
        passphrase, ok = QtGui.QInputDialog.getText(self, 'Passphrase',
                                                    'Enter your GPG passphrase:')

        return passphrase

def main():
    app = QtGui.QApplication(sys.argv)
    amon = Amon()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
