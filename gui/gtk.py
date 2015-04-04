from lib.version import AMON_VERSION
from lib.keybase import KeybaseUser
from lib.gmail import GmailUser
from lib.addresses import AddressBook
from lib.keybase import user_pub_key  # For debugging, to fetch default key to clean gpg slate
from lib.utils import zero_out
import lib.gpg as gpg

import sys
import json
import logging
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GObject, Gio, WebKit2
from os import rename
import thread
import time
import threading
import re
from pprint import pprint


GObject.threads_init()
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
    dialog = Gtk.Dialog("Please Enter Your Login", parent, Gtk.DialogFlags.MODAL |
                        Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.ButtonsType.OK_CANCEL)
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
    dialog = Gtk.Dialog("Please Enter Your GPG Passphrase", parent, Gtk.DialogFlags.MODAL |
                        Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.ButtonsType.OK_CANCEL)
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
        self.address_book = AddressBook()
        self.mailbox_list = Gtk.TreeStore(str, str)
        self.mailbox_view = None
        self.mailbox = None
        self.mail_list = Gtk.ListStore(str, str, str)
        self.mail_view = None
        self.config = {}
        self.window = None
        self.status_bar = None
        self.context_id = None
        self.error = None
        self.stop = False
        self.load_progress = None
        self.connect("activate", self.on_activate)

    def on_activate(self, data=None):
        logger.info("Starting up...")
        # a builder to add the UI designed with Glade to the grid
        builder = Gtk.Builder()
        # get the file (if it is there)
        try:
            builder.add_from_file("gui/AmonUI.glade")
        except IOError:
            print "File not found!"
            sys.exit()

        builder.connect_signals(self)
        self.window = builder.get_object("AmonWindow")
        self.status_bar = builder.get_object("statusbar")
        self.window.paned = builder.get_object("paned1")
        del builder

        self.window.set_title('Amon v' + AMON_VERSION)
        self.window.show_all()
        self.add_window(self.window)
        self.window.connect("destroy", self.on_quit)

        self.context_id = self.status_bar.get_context_id("statusbar")
        self.update_status_bar()

        def update_status_bar_thread():
            while True:
                GObject.idle_add(self.update_status_bar)
                time.sleep(0.5)

        thread.start_new_thread(update_status_bar_thread, ())

        # gpg.import_keys(user_pub_key('thorodinson'))  # Debug code to have public key for test
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
        self.create_mail_list()

    def create_mailbox_list(self):
        from gi.repository import Pango
        mailbox_view = Gtk.TreeView(model=self.mailbox_list)
        self.mailbox_view = mailbox_view
        mbox_list = self.gmail.get_mailbox_list(unread=True)
        iters = {}
        for i in range(len(mbox_list)):
            logger.debug(mbox_list[i][1:])
            if mbox_list[i][0] is not None:
                iters[mbox_list[i][1]] = self.mailbox_list.append(parent=iters[mbox_list[i][0]], row=mbox_list[i][1:])
            else:
                iters[mbox_list[i][1]] = self.mailbox_list.append(parent=None, row=mbox_list[i][1:])
        columns = ['Mailbox', 'Unread']
        for i in range(len(columns)):
            cell = Gtk.CellRendererText()
            if i == 0:
                cell.props.weight_set = True
                cell.props.weight = Pango.Weight.BOLD
            col = Gtk.TreeViewColumn(columns[i], cell, text=i)
            mailbox_view.append_column(col)

        self.window.paned.add1(mailbox_view)
        self.mailbox = 'INBOX'
        mailbox_view.get_selection().connect("changed", self.on_mailbox_changed)
        mailbox_view.show()

    def create_mail_list(self):
        vpaned = Gtk.VPaned()
        self.window.paned.add2(vpaned)

        scroll_win = Gtk.ScrolledWindow()
        scroll_win.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        treeview = Gtk.TreeView(model=self.mail_list)
        self.mail_view = treeview
        scroll_win.add(self.mail_view)

        update_mail_thread = threading.Thread(target=self.update_mail, args=())
        update_mail_thread.start()

        columns = ['From', 'Subject', 'UID']
        for i in range(len(columns)):
            cell = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(columns[i], cell, text=i)
            if columns[i] == 'UID':
                col.set_visible(False)
            treeview.append_column(col)

        treeview.connect("button-press-event", self.mail_clicked)

        vpaned.add1(scroll_win)
        vpaned.show_all()

    def update_mail(self):
        local_conn = self.gmail.imap_conn(self.config['email_pw'])
        done = False
        headers = None
        local_mailbox = None
        while not self.stop:
            if not local_mailbox == self.mailbox:
                local_mailbox = self.mailbox
                GObject.idle_add(self.mail_list.clear)
                headers = self.gmail.fetch_headers(self.mailbox, local_conn)
                done = False
            if not done:
                count = len(headers)
                for uid in reversed(headers):
                    row = self.gmail.get_mail_list_item(uid, local_conn)
                    logger.debug(self.stop)
                    if not self.mailbox == local_mailbox or self.stop:
                        break
                    GObject.idle_add(self.update_mail_list, row)
                    count -= 1
                    self.load_progress = "Fetching " + str(count) + " emails..."
                done = True

    def update_mail_list(self, row):
        self.mail_list.append(row)
        return False

    def on_quit(self, widget, parameter=None):
        self.stop = True
        sys.exit()

    def on_mailbox_changed(self, selection):
        store, it = selection.get_selected()
        self.mailbox = store[it][0]
        logger.debug("Selected mailbox: " + self.mailbox)

    def mail_clicked(self, widget, event):
        if event.button == 1 and event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS:
            selection = widget.get_selection()
            store, it = selection.get_selected()
            logger.debug("Double clicked: " + str(store[it]))
            uid = store[it][2]
            email = self.gmail.fetch_email(uid, self.mailbox)
            self.email_window(email=email)

    def email_window(self, typ=None, email=None):
        # Empty defaults
        textview = None
        send_btn = None
        # Handle case for email having been selected
        if email:
            pprint(email)
            title = email['headers']['Subject'][0]
            if typ == 'Reply':
                title = 'Re: ' + title
            elif typ == 'Forward':
                title = 'Fw: ' + title
        else:
            title = 'New Email'
        email_win = Gtk.Dialog(parent=self.window, flags=Gtk.DialogFlags.MODAL, title=title)
        email_win.set_default_size(800, 500)
        box = email_win.get_content_area()
        box.set_spacing(5)

        toolbar = Gtk.Toolbar(icon_size=1)
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        if typ is not None or email is None:
            header_entries = {}

        # Build email header details view
        # Case: displaying selected email
        label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        data_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        if email is not None and typ is None:
            headers = ['From', 'Subject', 'To']
            label_width = len(max(headers, key=len)) + 5
            for header in headers:
                header_label = Gtk.Label()
                header_label.set_markup(('<b>' + header + ':</b>').ljust(label_width, ' '))
                header_data = Gtk.Label(','.join(email['headers'][header]).replace('\n', ' ').replace('\r', ''))
                header_label.set_halign(Gtk.Align.START)
                header_data.set_halign(Gtk.Align.START)
                label_box.pack_start(header_label, False, False, 0)
                data_box.pack_start(header_data, False, False, 0)

            header_box.add(label_box)
            header_box.add(data_box)

            reply_btn = Gtk.ToolButton(label="_Reply", use_underline=True)
            reply_btn.connect('clicked', self.on_reply, email)
            forward_btn = Gtk.ToolButton(label="_Forward", use_underline=True)
            forward_btn.connect('clicked', self.on_forward, email)
            toolbar.insert(reply_btn, 0)
            toolbar.insert(forward_btn, 1)
        # Case: replying to selected email
        elif email is None or typ == 'Reply' or typ == 'Forward':
            headers = ['To', 'CC', 'BCC', 'Subject']
            label_width = len(max(headers, key=len)) + 5
            for header in headers:
                header_label = Gtk.Label()
                header_label.set_markup(('<b>' + header + ':</b>').ljust(label_width, ' '))
                header_entry = Gtk.Entry()
                if header == 'Subject':
                    if typ is not None:
                        pre = 'Re: ' if typ == 'Reply' else 'Fw: '
                        header_entry.set_text(pre +
                                              ','.join(email['headers'][header]).replace('\n', ' ').replace('\r', ''))
                header_label.set_halign(Gtk.Align.START)
                header_entry.set_halign(Gtk.Align.START)
                header_entry.set_width_chars(150)
                header_entries[header] = header_entry
                label_box.pack_start(header_label, True, False, 0)
                data_box.pack_start(header_entry, True, False, 0)

            header_box.add(label_box)
            header_box.add(data_box)

            send_btn = Gtk.ToolButton(label="_Send", use_underline=True)
            toolbar.insert(send_btn, 0)

        # Add toolbar and header information view
        box.add(toolbar)
        box.add(header_box)

        # Build email display/edit area
        email_scroll = Gtk.ScrolledWindow()
        email_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        # Set up email if this isn't a new email
        if email:
            webview = WebKit2.WebView()
            if typ in ['Reply', 'Forward']:
                webview.set_editable(True)
            for sub in email['body'].walk():
                if not sub.is_multipart():
                    # Required workaround until the binding for load_bytes() is available
                    # requires package only currently released for Ubuntu 15.04 (releases April 23, 2015)
                    if sub.get_content_type() == 'text/html':
                        webview.load_html(sub.get_payload(decode=True))
                    elif sub.get_content_type() == 'text/plain':
                        msg = sub.get_payload(decode=True)
                        if re.match(r'-----BEGIN PGP MESSAGE-----', msg):
                            pw = passphrase_dialog(email_win)
                            msg = gpg.decrypt_msg(msg, pw)
                            zero_out(pw)
                        webview.load_plain_text(msg)
            email_scroll.add(webview)
        else:
            textview = Gtk.TextView()
            email_scroll.add(textview)

        box.pack_start(email_scroll, True, True, 5)
        if send_btn:
            buf = textview.get_buffer()
            send_btn.connect('clicked', self.on_send,
                             [header_entries, buf, email_win])
        email_win.show_all()

    def on_new_email(self, widget, data=None):
        self.email_window()

    def on_reply(self, widget, data):
        self.email_window('Reply', data)

    def on_forward(self, widget, data):
        self.email_window('Forward', data)

    def on_send(self, widget, data):
        toaddr = None
        subject = None
        for header, entry in data[0].items():
            if header == 'To':
                toaddr = entry.get_text()
            elif header == 'CC':
                cc = entry.get_text()
            elif header == 'BCC':
                bcc = entry.get_text()
            elif header == 'Subject':
                subject = entry.get_text()
            else:
                raise Exception('Invalid email header ' + header + '!')

        buf = data[1]
        msg = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        # TODO: Implement CC and BCC fields
        self.gmail.send_email(toaddr, subject, msg)
        buf.delete(buf.get_start_iter(), buf.get_end_iter())
        zero_out(msg)
        data[2].destroy()

    def on_addresses(self, widget):
        address_win = Gtk.Dialog(parent=self.window, flags=Gtk.DialogFlags.MODAL, title='Address Book')
        address_win.set_default_size(200, 200)
        box = address_win.get_content_area()
        box.set_spacing(5)

        address_list = Gtk.TreeStore(str, str, str)
        address_view = Gtk.TreeView(model=address_list)
        addresses = self.address_book.get_contact_list()
        logger.debug('Addresses: ' + str(addresses))

        for name in addresses:
            tree_iter = address_list.append(parent=None, row=[name] + list(addresses[name]['primary']))
            for rec in addresses[name]['alts']:
                address_list.append(parent=tree_iter, row=[''] + list(rec))

        columns = ['Name', 'Email', 'Key Fingerprint']
        for i in range(len(columns)):
            cell = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(columns[i], cell, text=i)
            address_view.append_column(col)

        box.add(address_view)
        # address_view.get_selection().connect("changed", self.on_address_select)
        address_win.show_all()

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
        elif self.load_progress:
            text = self.load_progress
            self.load_progress = None
        else:
            text = None

        if text:
            self.status_bar.push(self.context_id, text)