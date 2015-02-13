from lib.version import AMON_VERSION
from lib.keybase import KeybaseUser
from lib.gmail import GmailUser
from lib.keybase import user_pub_key  # For debugging, to fetch default key to clean gpg slate
from lib.error import LoginError
from lib.utils import zero_out
import lib.gpg as gpg

import sys
import json
import logging
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, Pango
from os import rename
import thread, time

Gdk.threads_init()
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
        self.gmail = GmailUser()
        self.mailbox_view = None
        self.config = {}
        self.window = None
        self.status_bar = None
        self.context_id = None
        self.error = None
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
        self.status_bar = builder.get_object("statusbar")
        self.window.paned = builder.get_object("paned1")
        del builder

        self.window.show_all()
        self.add_window(self.window)

        self.context_id = self.status_bar.get_context_id("statusbar")
        self.update_status_bar()

        def update_status_bar_thread():
            while True:
                GObject.idle_add( self.update_status_bar )
                time.sleep(0.5)

        thread.start_new_thread(update_status_bar_thread, ())

        gpg.import_keys(user_pub_key('thorodinson'))  # Debug code to have public key for test
        passphrase = ""
        try:
            with open('amon.conf', 'r') as f:
                passphrase = passphrase_dialog(self.window)
                data = gpg.decrypt_msg(f.read(), passphrase)
                self.config = json.loads(data)
        except IOError:
            with open('test.conf', 'r') as f:
                data = f.read()
                self.config = json.loads(data)
        finally:
            zero_out(passphrase)

        if not self.config['keybase_user'] == '' and not self.config['keybase_pw'] == '':
            self.keybase_user.login(self.config['keybase_user'], self.config['keybase_pw'])

        if not self.config['email_addr'] == '' and not self.config['email_pw'] == '':
            self.gmail.login(self.config['email_addr'], self.config['email_pw'])

        self.create_mailbox_list()

        vpaned = Gtk.VPaned()
        self.window.paned.add2(vpaned)

        scroll_win = Gtk.ScrolledWindow()
        scroll_win.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        mail_model = Gtk.ListStore(str, str)
        mail_view = Gtk.TreeView(model=mail_model)
        scroll_win.add_with_viewport(mail_view)

        # for i in range(10):
        #     msg_info = ["test@gmail.com", "Testing " + str(i)]
        #     mail_model.append(msg_info)

        columns = ['From', 'Subject']
        for i in range(len(columns)):
            cell = Gtk.CellRendererText()
            # if i == 0:
            #     cell.props.weight_set = True
            #     cell.props.weight = Pango.Weight.BOLD
            col = Gtk.TreeViewColumn(columns[i], cell, text=i)
            mail_view.append_column(col)

        vpaned.add1(scroll_win)

    def create_mailbox_list(self):
        mailbox_list = Gtk.TreeStore(str, str)
        mailbox_view = Gtk.TreeView(model=mailbox_list)
        self.mailbox_view = mailbox_view
        mbox_list = self.gmail.get_mailbox_list(unread=True)
        iters = {}
        for i in range(len(mbox_list)):
            logger.debug(mbox_list[i][1:])
            if mbox_list[i][0] is not None:
                iters[mbox_list[i][1]] = mailbox_list.append(parent=iters[mbox_list[i][0]], row=mbox_list[i][1:])
            else:
                iters[mbox_list[i][1]] = mailbox_list.append(parent=mbox_list[i][0], row=mbox_list[i][1:])
        columns = ['Mailbox', 'Unread']
        for i in range(len(columns)):
            cell = Gtk.CellRendererText()
            if i == 0:
                cell.props.weight_set = True
                cell.props.weight = Pango.Weight.BOLD
            col = Gtk.TreeViewColumn(columns[i], cell, text=i)
            mailbox_view.append_column(col)

        self.window.paned.add1(mailbox_view)
        mailbox_view.get_selection().connect("changed", self.on_changed)
        mailbox_view.show()

    def gtk_main_quit(self, widget):
        sys.exit()

    def on_changed(self, selection):
        store, it = selection.get_selected()
        mbox = store[it][0]
        logger.debug("Selected mailbox: " + mbox)
        # mail = self.gmail.fetch_headers(mbox)

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
        dialog.set_border_width(10)

        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_PREFERENCES, Gtk.IconSize.DIALOG)
        image.show()
        dialog.set_image(image)
        dialog.set_title(APP_NAME + " Preferences")

        vbox = dialog.vbox
        dialog.set_default_response(Gtk.ResponseType.OK)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        vbox.pack_start(listbox, True, True, 0)

        row = Gtk.ListBoxRow()
        kb_user = Gtk.HBox()
        row.add(kb_user)
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
        listbox.add(row)

        row = Gtk.ListBoxRow()
        kb_pw = Gtk.HBox()
        row.add(kb_pw)
        kb_pw_entry = Gtk.Entry()
        kb_pw_entry.set_visibility(False)
        kb_pw_label = Gtk.Label(label='New Keybase Password:')
        kb_pw_label.set_size_request(150, 10)
        kb_pw.pack_start(kb_pw_label, False, False, 10)
        kb_pw_entry.set_text("")
        kb_pw_entry.connect('activate',
                            lambda entry, dialog, response: dialog.response(response), dialog, Gtk.ResponseType.OK)
        kb_pw.pack_start(kb_pw_entry, False, False, 10)
        add_help_button(kb_pw, "Enter Keybase Password")
        listbox.add(row)

        row = Gtk.ListBoxRow()
        addr = Gtk.HBox()
        row.add(addr)
        addr_entry = Gtk.Entry()
        addr_label = Gtk.Label(label='Email address:')
        addr_label.set_size_request(150, 10)
        addr.pack_start(addr_label, False, False, 10)
        addr_entry.set_text(self.config['email_addr'])
        addr_entry.connect('activate',
                           lambda entry, dialog, response: dialog.response(response), dialog, Gtk.ResponseType.OK)
        addr.pack_start(addr_entry, False, False, 10)
        add_help_button(addr, "Email address. (Currently only supports Gmail.)")
        listbox.add(row)

        row = Gtk.ListBoxRow()
        email_pw = Gtk.HBox()
        row.add(email_pw)
        email_pw_entry = Gtk.Entry()
        email_pw_entry.set_visibility(False)
        email_pw_label = Gtk.Label(label='New Email Password:')
        email_pw_label.set_size_request(150, 10)
        email_pw.pack_start(email_pw_label, False, False, 10)
        email_pw_entry.set_text("")
        email_pw_entry.connect('activate',
                               lambda entry, dialog, response: dialog.response(response), dialog, Gtk.ResponseType.OK)
        email_pw.pack_start(email_pw_entry, False, False, 10)
        add_help_button(email_pw, "Enter Email Password")
        listbox.add(row)

        dialog.show_all()
        r = dialog.run()

        keybase_user = kb_user_entry.get_text()
        keybase_pw = kb_pw_entry.get_text()
        address = addr_entry.get_text()
        email_pass = email_pw_entry.get_text()
        dialog.destroy()
        if r == Gtk.ResponseType.CANCEL:
            zero_out(keybase_pw)
            zero_out(email_pass)
            return

        if keybase_user != '':
            self.config['keybase_user'] = keybase_user
        if keybase_pw != '':
            self.config['keybase_pw'] = keybase_pw
        if address != '':
            self.config['email_addr'] = address
        if email_pass != '':
            self.config['email_pw'] = email_pass

        with open('amon.conf', 'w+b') as f:
            json.dump(self.config, f)
            f.seek(0)
            gpg.encrypt_msg(f, self.config['email_addr'])
        rename('enc_msg.gpg', 'amon.conf')

        if self.config['keybase_pw'] != '':
            logger.debug("Logging in user " + self.config['keybase_user'] + " with password " + self.config['keybase_pw'])
            self.keybase_user.login(self.config['keybase_user'], self.config['keybase_pw'])

        zero_out(keybase_pw)
        zero_out(email_pass)

        logger.debug("Set keybase user to " + keybase_user)
        logger.debug("Set email address to " + address)
        logger.info("Updated preference settings.")

    def on_close(self, action, parameter):
        action.destroy()

    def on_keybase_signup(self, widget):
        # TODO: logic for keybase signup
        pass

    def update_status_bar(self):

        if self.error:
            text = self.error
        elif self.keybase_user.updated():
            text = self.keybase_user.get_status()
            self.keybase_user.reset_status()
        else:
            text = None

        if text:
            self.status_bar.push(self.context_id, text)