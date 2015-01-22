from lib import keybase
import gnupg
from os import system
from pprint import pprint
import triplesec
import msgpack
from base64 import b64decode
from binascii import hexlify, unhexlify

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
system('rm -rf /home/testgpguser/gpghome')  # clean GPG test directory before proceeding with test
gpg = gnupg.GPG(gnupghome='/home/testgpguser/gpghome')
user = raw_input("Username: ")
salt = keybase.get_salt(user)

pw = raw_input("Password: ")
ts = triplesec.TripleSec(key=pw)
login_reply = keybase.login(user, pw, salt["salt"], salt["session"])
me = login_reply['me']
session = login_reply['session']

# user_priv_key = me['private_keys']['primary']['bundle']
# json_priv_key = msgpack.unpackb(b64decode(user_priv_key))
# pprint(json_priv_key)
# print '\n'
#
# enc = json_priv_key['body']['priv']['data']
# print ts.decrypt(enc)

keys = keybase.key_fetch(me['public_keys']['primary']['kid'], ['sign'], session)
print keys
# import_result = gpg.import_keys(user_priv_key)
# pprint(import_result.results)


