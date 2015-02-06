from lib.version import AMON_VERSION
from lib.keybase import KeybaseUser
from lib.error import LoginError
from lib.utils import zero_out
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio

APP_NAME = "Amon"
import platform
MONOSPACE_FONT = "Lucida Console" if platform.system() == 'Windows' else 'monospace'


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


class Amon(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id="apps.test.amon")
        self.keybase_user = KeybaseUser()
        self.window = None
        self.connect("activate", self.on_activate)

    def on_activate(self, data=None):
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
        message = "Here are the current settings. For more explanation, " \
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
        address = addr_entry.get_text()
        print address

        dialog.destroy()
        if r == Gtk.ResponseType.CANCEL:
            return

        print "OK was pressed!"

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