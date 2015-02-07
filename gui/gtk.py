from lib.version import AMON_VERSION
from lib.keybase import KeybaseUser
from lib.error import LoginError
from lib.utils import zero_out
import lib.gpg as gpg

import sys
import json
import logging
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

APP_NAME = "Amon"
import platform
MONOSPACE_FONT = "Lucida Console" if platform.system() == 'Windows' else 'monospace'
logger = logging.getLogger(__name__)


def show_message(message, parent=None):
    dialog = Gtk.MessageDialog(parent=parent, flags=Gtk.DialogFlags.MODAL,
                               buttons=Gtk.ButtonsType.CLOSE, message_format=message)
    dialog.show()
    dialog.run()
    dialog.destroy()


def add_help_button(hbox, message):
    button = Gtk.Button('?')
    button.connect("clicked", lambda x: show_message(message))
    button.show()
    hbox.pack_start(button, False, False, 0)


def username_line(label):
    username = Gtk.HBox()

    # username label
    user_label = Gtk.Label(label=label)
    user_label.set_size_request(120, 10)
    user_label.show()
    username.pack_start(user_label, False, False, 10)

    # username entry
    user_entry = Gtk.Entry()
    user_entry.set_size_request(300, -1)
    user_entry.show()
    username.pack_start(user_entry, False, False, 10)
    username.show()
    return username, user_entry


def password_line(label):
    password = Gtk.HBox()

    # password label
    password_label = Gtk.Label(label=label)
    password_label.set_size_request(120, 10)
    password_label.show()
    password.pack_start(password_label, False, False, 10)

    # password entry
    password_entry = Gtk.Entry()
    password_entry.set_size_request(300, -1)
    password_entry.set_visibility(False)
    password_entry.show()
    password.pack_start(password_entry, False, False, 10)
    password.show()
    return password, password_entry


def login_dialog(parent):
    dialog = Gtk.Dialog("Please Enter Your Login", parent, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.ButtonsType.OK_CANCEL)
    # dialog.get_image().set_visible(False)
    current_user, current_user_entry = username_line("Username: ")
    current_user_entry.connect('activate',
                               lambda entry, dialog, response: dialog.response(response), dialog, Gtk.ResponseType.OK)
    dialog.vbox.pack_start(current_user, False, True, 0)
    current_pw, current_pw_entry = password_line("Password: ")
    current_pw_entry.connect("activate",
                             lambda entry, dialog, response: dialog.response(response), dialog, Gtk.ResponseType.OK)
    dialog.vbox.pack_start(current_pw, False, True, 0)
    dialog.show()
    result = dialog.run()
    user = current_user_entry.get_text()
    pw = current_pw_entry.get_text()
    dialog.destroy()
    if result != Gtk.ResponseType.CANCEL:
        return user, pw
    else:
        return None, None


def passphrase_dialog(parent):
    dialog = Gtk.Dialog("Please Enter Your GPG Passphrase", parent, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.ButtonsType.OK_CANCEL)
    # dialog.get_image().set_visible(False)
    current_pw, current_pw_entry = password_line("Passphrase: ")
    current_pw_entry.connect("activate",
                             lambda entry, dialog, response: dialog.response(response), dialog, Gtk.ResponseType.OK)
    dialog.vbox.pack_start(current_pw, False, True, 0)
    dialog.show()
    result = dialog.run()
    pw = current_pw_entry.get_text()
    dialog.destroy()
    if result != Gtk.ResponseType.CANCEL:
        return pw
    else:
        return None


class Amon(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id="apps.test.amon")
        self.keybase_user = KeybaseUser()
        self.config = {}
        self.window = None
        self.connect("activate", self.on_activate)

    def on_activate(self, data=None):
        logger.info("Starting up...")
        # a builder to add the UI designed with Glade to the grid
        builder = Gtk.Builder()
        # get the file (if it is there)
        try:
            builder.add_from_file("gui/AmonUI.glade")
        except:
            print "File not found!"
            sys.exit()

        builder.connect_signals(self)
        self.window = builder.get_object("AmonWindow")
        self.window.status_bar = builder.get_object("statusbar")
        del builder

        self.window.show()
        self.add_window(self.window)

        passphrase = passphrase_dialog(self.window)
        try:
            with open('amon.conf', 'r') as f:
                data = gpg.decrypt_msg(f.read(), passphrase)
                self.config = json.loads(data)
        except IOError:
            self.config = {'keybase_user': '', 'keybase_pw': '', 'email_addr': '', 'email_pw': ''}
        finally:
            zero_out(passphrase)

        if not self.config['keybase_user'] == '' and not self.config['keybase_pw'] == '':
            self.keybase_user.login(config['keybase_user'], config['keybase_pw'])

    def gtk_main_quit(self, widget):
        sys.exit()

    def on_about(self, widget):
        about_dialog = Gtk.AboutDialog()

        authors = ["Matt Tanous"]

        about_dialog.set_program_name("Amon " + AMON_VERSION)
        about_dialog.set_authors(authors)
        about_dialog.set_website("https://github.com/CodingAnarchy/Amon")
        about_dialog.set_website_label("GitHub Source Code Repository")

        about_dialog.connect("response", self.on_close)
        about_dialog.show()

    def on_pref(self, widget):
        message = "Here are the current settings (stored as encrypted data in amon.conf). For more explanation, " \
                  "click on the question mark buttons next to the input field."

        dialog = Gtk.MessageDialog(parent=self.window, flags=Gtk.DialogFlags.MODAL,
                                   buttons=Gtk.ButtonsType.OK_CANCEL, message_format=message)

        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_PREFERENCES, Gtk.IconSize.DIALOG)
        image.show()
        dialog.set_image(image)
        dialog.set_title(APP_NAME + " Preferences")

        vbox = dialog.vbox
        dialog.set_default_response(Gtk.ResponseType.OK)

        kb_user = Gtk.HBox()
        kb_user_entry = Gtk.Entry()
        kb_user_label = Gtk.Label(label='Keybase Username:')
        kb_user_label.set_size_request(150, 10)
        kb_user_label.show()
        kb_user.pack_start(kb_user_label, False, False, 10)
        kb_user_entry.set_text(self.config['keybase_user'])
        kb_user_entry.connect('activate',
                              lambda entry, dialog, response: dialog.response(response), dialog, Gtk.ResponseType.OK)
        kb_user_entry.show()
        kb_user.pack_start(kb_user_entry, False, False, 10)
        add_help_button(kb_user, "Keybase User ID")
        kb_user.show()
        vbox.pack_start(kb_user, False, False, 5)

        kb_pw = Gtk.HBox()
        kb_pw_entry = Gtk.Entry()
        kb_pw_entry.set_visibility(False)
        kb_pw_label = Gtk.Label(label='New Keybase Password:')
        kb_pw_label.set_size_request(150, 10)
        kb_pw_label.show()
        kb_pw.pack_start(kb_pw_label, False, False, 10)
        kb_pw_entry.set_text("")
        kb_pw_entry.connect('activate',
                            lambda entry, dialog, response: dialog.response(response), dialog, Gtk.ResponseType.OK)
        kb_pw_entry.show()
        kb_pw.pack_start(kb_pw_entry, False, False, 10)
        add_help_button(kb_pw, "Enter Keybase Password")
        kb_pw.show()
        vbox.pack_start(kb_pw, False, False, 5)

        addr = Gtk.HBox()
        addr_entry = Gtk.Entry()
        addr_label = Gtk.Label(label='Email address:')
        addr_label.set_size_request(150, 10)
        addr_label.show()
        addr.pack_start(addr_label, False, False, 10)
        addr_entry.set_text("")
        addr_entry.connect('activate',
                           lambda entry, dialog, response: dialog.response(response), dialog, Gtk.ResponseType.OK)
        addr_entry.show()
        addr.pack_start(addr_entry, False, False, 10)
        add_help_button(addr,
                        "Email address for sending and receiving encrypted emails. (Currently only supports Gmail.)")
        addr.show()
        vbox.pack_start(addr, False, False, 5)

        dialog.show()
        r = dialog.run()

        keybase_user = kb_user_entry.get_text()
        keybase_pw = kb_pw_entry.get_text()
        address = addr_entry.get_text()
        dialog.destroy()
        if r == Gtk.ResponseType.CANCEL:
            zero_out(keybase_pw)
            return

        self.config['keybase_user'] = keybase_user
        self.config['email_address'] = address
        zero_out(keybase_pw)
        logger.debug("Set keybase user to " + keybase_user)
        logger.debug("Set email address to " + address)
        logger.info("Updated preference settings.")

    def on_close(self, action, parameter):
        action.destroy()

    def on_keybase_login(self, widget):
        login_success = False
        login_attempts = 0
        user = None
        context_id = self.window.status_bar.get_context_id("login")
        self.window.status_bar.push(context_id, "Logging in...")
        while not login_success and login_attempts < 3:
            user, password = login_dialog(self.window)
            if user is not None:
                try:
                    self.keybase_user.login(user, password)
                    login_success = True
                except LoginError:
                    login_attempts += 1
                    pass
                finally:
                    zero_out(password)  # Shouldn't be necessary, but just to make sure
            else:
                # TODO: Cancelled out of login - handle appropriately
                sys.exit()
        if login_attempts >= 3:
            raise LoginError("Attempted keybase login too many times. Aborting.")
        self.window.status_bar.push(context_id, "Logged in as " + user + ".")