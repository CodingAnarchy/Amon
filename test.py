import sys
from gui.gtk import Amon
from lib import gpg
from lib import keybase
from lib.gmail import GmailUser
import json
import logging
import logging.config

logger = logging.getLogger(__name__)

with open('logging.json', 'r') as f:
    data = f.read()
    conf = json.loads(data)

logging.config.dictConfig(conf)


# keys, csrf = amon.key_fetch(me['private_keys']['primary']['kid'], ['sign'], session)

# Test code for obtaining a user's public key
pub_key = keybase.user_pub_key('christopherburg')
gpg.import_keys(pub_key)
pub_key = keybase.user_pub_key('thorodinson')
gpg.import_keys(pub_key)

# print gpg.list_keys(True)

# sign = gpg.sign_msg('A simple test of signing a message!')
# print sign
#
# verified = gpg.verify_msg(sign)

# test = gpg.export_keys(to)
# print test

# results = amon.user_autocomplete('thor')
# for u in results:
#     print u['components']['username']['val']

# them = amon.user_lookup('domain', 'christopherburg.com', 'pictures')
# pprint(them)

# amon.edit_profile(name="Matt Tanous",
#                      bio="Anarchist working to develop a digital end-run around the state.",
#                      loc='United States')

# amon.kill_sessions()

# email = raw_input('Email Address: ')
# pw = raw_input('Email Password: ')
# gmail = GmailUser(email, pw)
# mbox = gmail.get_mailbox_list()

app = Amon()
response = app.run()
sys.exit(response)

# new_key = gpg.gen_key(name_real='Matt Tanous', name_email='mtanous22@gmail.com', passphrase='test')
# print new_key
#
# with open('test.txt', 'rb') as f:
#     enc = gpg.encrypt_msg(f, 'mtanous22@gmail.com')
#
# with open('enc_msg.gpg', 'rb') as f:
#     dec = gpg.decrypt_msg(f, 'test')
#
# with open('dec_msg.txt', 'rb') as f:
#     msg = f.read()
#     print msg
#
# gpg.delete_keys(new_key)

