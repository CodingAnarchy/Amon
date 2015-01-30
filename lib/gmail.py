# Some code and comments for fetching and parsing email taken from following URL
# https://github.com/neumark/gmail_fetcher/blob/afcfb504b3f9f995801d2a5deedbf3095439cf84/fetcher.py

import smtplib
import imaplib
import email
import email.header
import datetime
import re
import quopri
import pprint
from HTMLParser import HTMLParser

gm_header_re = re.compile("^(\d+) \(X-GM-THRID (\d+) X-GM-MSGID (\d+) X-GM-LABELS "
                          "\(([^\)]*)\) UID (\d+) RFC822 {(\d+)}$")


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
        'body': get_first_text_block(),
        'raw': full_msg
    }


def fetch_email(mail, uid):
    result, data = mail.uid('fetch', uid, '(RFC822 X-GM-THRID X-GM-MSGID X-GM-LABELS X-GM-MSGID)')
    return data


def make_query():
    # return '(SENTSINCE {startdate}) (SENTBEFORE {enddate})'.format(
    #     startdate=(datetime.date.today() - datetime.timedelta(1)).strftime("%d-%b-%Y"),
    #     enddate=(datetime.date.today()).strftime("%d-%b-%Y")
    # )
    return '(SENTSINCE "01-JAN-2015" BODY "BEGIN PGP")'


def auth():
    imapquery = make_query()
    print "IMAP query is " + imapquery
    # No proxy - requires changes for proxy ('localhost', <forwarded port>)
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    user = raw_input("Please enter your email address: ")
    pw = raw_input("Please enter your password: ")
    mail.login(user, pw)
    # Out: list of "folders" (labels in gmail)
    mail.select('"[Gmail]/All Mail"')  # connect to "All Mail" folder
    status, data = mail.uid('search', None, imapquery)
    results = data[0].split()
    print results
    print "IMAP Server returned " + str(len(results)) + " results"
    pp = pprint.PrettyPrinter(indent=4)
    print pp.pformat([parse_email(fetch_email(mail, i))['body'] for i in results])


def send_email(fromaddr, toaddr, msg):
    # Credentials (needed for login)
    user = raw_input("Email address: ")
    password = raw_input("Password: ")

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(user, password)
    server.sendmail(fromaddr, toaddr, msg)
    server.quit()