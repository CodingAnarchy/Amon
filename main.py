from lib import keybase, gpg
from pprint import pprint
import triplesec


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

# Log in and get session idea
user = raw_input("Username: ")
salt = keybase.get_salt(user)

pw = raw_input("Password: ")
ts = triplesec.TripleSec(key=pw)
login_reply = keybase.login(user, pw, salt["salt"], salt["session"])
me = login_reply['me']
session = login_reply['session']

keys = keybase.key_fetch(me['private_keys']['primary']['kid'], ['sign'], session)
pub_key = me['public_keys']['primary']['bundle']

# Test code for obtaining a user's public key
pub_key = keybase.user_pub_key('thorodinson')
import_result = gpg.import_keys(pub_key)
pprint(import_result.results)

priv_key = keybase.decode_priv_key(me['private_keys']['primary']['bundle'], ts)
import_result = gpg.import_keys(priv_key)
pprint(import_result.results)

print gpg.list_keys()

to = import_result.fingerprints[0]
test = gpg.export_keys(to)

enc = gpg.encrypt_msg('A simple test', to)
print enc

dec = gpg.decrypt_msg(enc)
print dec


