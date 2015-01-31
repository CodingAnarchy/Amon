from version import AMON_VERSION
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, cairo

Gdk.threads_init()
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
    dialog = Gtk.MessageDialog(parent, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                               Gtk.MessageType.QUESTION, Gtk.ButtonsType.OK_CANCEL, "Please enter your password.")
    dialog.get_image().set_visible(False)
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


class AmonWindow:

    def show_message(self, msg):
        show_message(msg, self.window)

    def __init__(self):
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        title = APP_NAME + ' v' + AMON_VERSION
        self.window.set_title(title)
        self.window.connect("destroy", Gtk.main_quit)
        self.window.set_border_width(0)
        self.window.set_default_size(720, 350)

        user, password = login_dialog(self.window)
        self.window.show_all()
        print user
        print password

win = AmonWindow()
Gtk.main()