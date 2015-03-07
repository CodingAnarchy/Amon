# Some code and comments for fetching and parsing email taken from following URL
# https://github.com/neumark/gmail_fetcher/blob/afcfb504b3f9f995801d2a5deedbf3095439cf84/fetcher.py

import smtplib
import imaplib
import email
import email.header
from email.mime.text import MIMEText
import datetime
import re
import quopri
import pprint
import logging
from HTMLParser import HTMLParser

gm_header_re = re.compile("^(\d+) \(X-GM-THRID (\d+) X-GM-MSGID (\d+) X-GM-LABELS "
                          "\(([^\)]*)\) UID (\d+) RFC822 {(\d+)}$")
list_response_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')

logger = logging.getLogger(__name__)


def parse_email(full_msg):
    raw = full_msg[0][1]
    gm_headers = full_msg[0][0]
    # flags = full_msg[1]
    email_msg = email.message_from_string(raw)

    # note that if you want to get text content (body) and the email contains
    # multiple payloads (plaintext/html), you must parse each message separately
    # use something like the following (taken from stackoverflow post)
    def parse_headers():
        global gm_header_re
        hdict = {}
        for hdr, val in email_msg.items():
            for decoded_val in email.header.decode_header(val):
                hdict.setdefault(hdr, []).append(unicode(decoded_val[0],
                                                         decoded_val[1] if decoded_val[1] is not None else 'utf-8'))
        groups = gm_header_re.match(gm_headers).groups()
        hdict['X-GM-THRID'] = groups[1]
        hdict['X-GM-MSGID'] = groups[2]
        hdict['X-GM-LABELS'] = groups[3]
        hdict['IMAP-UID'] = groups[4]
        return hdict

    def get_first_text_block():
        def toutf(part):
            charset = part.get_content_charset() if part.get_content_charset() is not None else 'utf-8'
            s = part.get_payload(decode=True)
            t = part.get_content_type()
            if t == "text/html":
                h = HTMLParser()
                return h.unescape(unicode(s, charset))
            elif t == "text/plain":
                return unicode(s, charset)
            else:
                return unicode(quopri.decodestring(s), charset)
        maintype = email_msg.get_content_maintype()
        if maintype == 'multipart':
            for part in email_msg.get_payload():
                if part.get_content_maintype() == 'text':
                    return toutf(part)
                elif maintype == 'text':
                    return toutf(email_msg)
        else:
            return toutf(email_msg)

    # print email_msg['To']
    # print email.utils.parseaddr(email_msg['From'])
    return {
        'headers': parse_headers(),
        # 'body': get_first_text_block(),
        'body': email_msg,
    }


def make_query():
    # return '(SENTSINCE {startdate}) (SENTBEFORE {enddate})'.format(
    #     startdate=(datetime.date.today() - datetime.timedelta(1)).strftime("%d-%b-%Y"),
    #     enddate=(datetime.date.today()).strftime("%d-%b-%Y")
    # )
    return '(SENTSINCE "01-JAN-2015" BODY "BEGIN PGP")'


def parse_list_response(line):
    flags, delimiter, mailbox_name = list_response_pattern.match(line).groups()
    mailbox_name = mailbox_name.strip('"')
    return flags, delimiter, mailbox_name


class GmailUser():
    def __init__(self):
        self.email = None
        self.smtp_server = smtplib.SMTP('smtp.gmail.com:587')
        self.imap = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        self.mailboxes = []

    def login(self, email, pw):
        self.email = email
        self.smtp_server.starttls()
        self.smtp_server.login(self.email, pw)
        self.imap.login(self.email, pw)

    def imap_conn(self, pw):
        local_conn = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        local_conn.login(self.email, pw)
        return local_conn

    def send_email(self, to, subject, msg):
        # TODO: Implement Subject, CC and BCC headers
        msg = MIMEText(msg)
        msg['Subject'] = subject
        msg['From'] = self.email
        msg['To'] = to
        self.smtp_server.sendmail(self.email, [to], msg.as_string())

    def fetch_email(self, uid, folder='Inbox'):
        self.imap.select(folder)
        result, data = self.imap.uid('fetch', uid, '(RFC822 X-GM-THRID X-GM-MSGID X-GM-LABELS X-GM-MSGID)')
        return parse_email(data)

    def fetch_headers(self, folder='INBOX', conn=None):
        if conn is None:
            conn = self.imap
        # Get path to mailbox needed for fetching from IMAP
        # Search through list of lists for folder, join it to parent path if it exists
        path = next((temp[:] for x, temp in enumerate(self.mailboxes) if temp[1] == folder), folder)
        mbox = '/'.join(path) if path[0] is not "" else path[1]
        logger.debug("Found mailbox " + mbox)
        conn.select(mbox, readonly=True)
        result, data = conn.uid('search', None, "ALL")
        id_list = data[0].split()
        logger.debug("Returned " + str(len(id_list)) + " email ids.")
        return id_list

    def get_mail_list_item(self, uid, conn=None):
        if conn is None:
            conn = self.imap
        logger.debug(uid)
        result, data = conn.uid('fetch', uid, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM)])')
        if result == 'OK':
            header = data[0][1].split('\r\n')
            sender = [s for s in header if "From: " in s or "FROM: " in s][0]
            try:
                subject = [s for s in header if "Subject: " in s or "SUBJECT: " in s][0]
            except IndexError:
                subject = ""
            sender = re.sub(r'^(?i)from: |"', '', sender)
            subject = re.sub(r'^(?i)subject: |"', '', subject)
            sender, enc = email.header.decode_header(sender)[0]
            subject, enc = email.header.decode_header(subject)[0]
            row = [sender, subject, uid]
            logger.debug(row)
            return row

    def get_mail_count(self, folder='Inbox'):
        # Get path to mailbox needed for fetching from IMAP
        # Search through list of lists for folder, join it to parent path if it exists
        path = next((temp[:] for x, temp in enumerate(self.mailboxes) if temp[1] == folder), folder)
        mbox = '/'.join(path) if path[0] is not "" else path[1]
        rc, count = self.imap.select(mbox, readonly=True)
        return count[0]

    def get_unread_count(self, folder='Inbox'):
        logger.debug("Getting unread message count for " + folder)
        rc, message = self.imap.status(folder, "(UNSEEN)")
        try:
            unread = re.search("UNSEEN (\d+)", message[0]).group(1)
        except AttributeError:
            unread = ""
        return unread

    def get_mailbox_list(self, unread=False):
        logger.info("Getting mailbox list...")
        mailboxes = []
        typ, data = self.imap.list()
        logger.info("Response code: " + typ)
        for idx, line in enumerate(data):
            data[idx] = parse_list_response(line)
            path = data[idx][2].split(data[idx][1])
            box_name = path[-1]
            self.mailboxes.append(['/'.join(path[:-1]), box_name])
            if len(path) > 1:
                parent = path[-2]
            else:
                parent = None
            if unread:
                unseen = self.get_unread_count('/'.join(path))
                logger.debug("Mailbox " + box_name + " has " + unseen + " unread messages.")
                mailboxes.append([parent, box_name, unseen])
            else:
                mailboxes.append([parent, box_name])
        logger.debug('Response:' + pprint.pformat(data))
        return mailboxes