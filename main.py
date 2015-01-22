from lib import keybase
import gnupg
from os import system
from pprint import pprint
import triplesec
import msgpack
from base64 import b64decode, b64encode
from binascii import hexlify, unhexlify

# clean GPG test directory before proceeding with test
system('rm -rf /home/testgpguser/gpghome')
gpg = gnupg.GPG(gnupghome='/home/testgpguser/gpghome')

# Test code for use with user lookup
# lookup = 'temp'
# users = []
# fields = 'basics'
# while lookup != '':
#     lookup = raw_input("User to look up: ")
#     if lookup != '':
#         users.append(lookup)
#
# status = keybase.user_lookup('domain', users, fields)
# print status['status']

# Test code for obtaining a user's public key
# pub_key = keybase.user_pub_key('thorodinson')
# print pub_key

# Log in and import private key of logged in user
user = raw_input("Username: ")
salt = keybase.get_salt(user)

pw = raw_input("Password: ")
ts = triplesec.TripleSec(key=pw)
login_reply = keybase.login(user, pw, salt["salt"], salt["session"])
me = login_reply['me']
session = login_reply['session']

keys = keybase.key_fetch(me['private_keys']['primary']['kid'], ['sign'], session)
enc = msgpack.unpackb(b64decode(keys[0]['bundle']))
enc = enc['body']['priv']['data']
priv_key = ts.decrypt(enc)
import_result = gpg.import_keys(priv_key)
pprint(import_result.results)


