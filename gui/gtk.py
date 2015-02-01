from lib.version import AMON_VERSION
from lib.keybase import KeybaseUser
from lib.error import LoginError
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


# class Amon(Gtk.Application):
#     def __init__(self):
#         Gtk.Application.__init__(self, application_id="apps.test.amon")
#         self.kb_user = None
#         self.window = None
#         self.connect("activate", self.on_activate)
#
#     def on_activate(self, data=None):
#         # a builder to add the UI designed with Glade to the grid
#         builder = Gtk.Builder()
#         # get the file (if it is there)
#         try:
#             builder.add_from_file("gui/AmonUI.glade")
#         except:
#             print "File not found!"
#             sys.exit()
#
#         builder.connect_signals(self)
#         self.window = builder.get_object("AmonWindow")
#         del builder
#
#         self.window.show()
#         self.add_window(self.window)
#
#     def gtk_main_quit(self, widget):
#         sys.exit()


class AmonWindow(Gtk.Window):
    def show_message(self, msg):
        show_message(msg, self.window)

    def on_key(self, w, event):
        if Gdk.ModifierType.CONTROL_MASK & event.state and event.keyval in [113, 119]:
            Gtk.main_quit()
        return True

    def __init__(self):
        self.keybase_user = None
        self.email_type = 'Gmail'
        self.email_user = None

        title = APP_NAME + ' v' + AMON_VERSION
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL, title=title)
        self.window.connect("destroy", Gtk.main_quit)
        self.window.connect("key-press-event", self.on_key)
        self.window.set_border_width(0)
        self.window.set_default_size(720, 350)

        vbox = Gtk.VBox()

        self.status_bar = Gtk.Statusbar()
        vbox.pack_start(self.status_bar, False, False, 0)

        # self.status_image = Gtk.Image()
        # self.status_image.set_from_stock(Gtk.STOCK_NO, Gtk.IconSize.MENU)
        # self.status_image.set_alignment(True, 0.5)
        # self.status_image.show()

        self.login_button = Gtk.Button()
        login_label = Gtk.Label("_Login", use_underline=True)
        self.login_button.connect("clicked", lambda x: self.login())
        self.login_button.add(login_label)
        self.login_button.set_relief(Gtk.ReliefStyle.NONE)
        self.login_button.show()
        self.status_bar.pack_start(self.login_button, False, False, 0)

        self.window.add(vbox)
        self.window.show_all()

    def login(self):
        login_success = False
        login_attempts = 0
        while not login_success and login_attempts < 3:
            user, password = login_dialog(self.window)
            if user is not None:
                try:
                    self.keybase_user = KeybaseUser(user, password)
                    login_success = True
                except LoginError:
                    login_attempts += 1
                    pass
            else:
                # TODO: Cancelled out of login - handle appropriately
                sys.exit()
        if login_attempts >= 3:
            raise LoginError("Attempted keybase login too many times. Aborting.")


class AmonGui:
    def __init__(self):
        self.window = AmonWindow()

    def main(self):
        # TODO - handle start up details

        Gtk.main()