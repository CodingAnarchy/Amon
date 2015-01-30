from lib import keybase, gpg, gmail
from pprint import pprint
import triplesec


# Log in and get session idea
user = raw_input("Username: ")
pw = raw_input("Password: ")
ts = triplesec.TripleSec(key=pw)
me = keybase.login(user, pw)

# keys, csrf = keybase.key_fetch(me['private_keys']['primary']['kid'], ['sign'], session)
# pub_key = me['public_keys']['primary']['bundle']

# Test code for obtaining a user's public key
# pub_key = keybase.user_pub_key('christopherburg')
# import_result = gpg.import_keys(pub_key)
# pprint(import_result.results)

# print priv_key

priv_key = keybase.decode_priv_key(me['private_keys']['primary']['bundle'], ts)
import_result = gpg.import_keys(priv_key)
# pprint(import_result.results)
to = import_result.fingerprints[0]


# print gpg.list_keys(True)

# test = gpg.export_keys(to)
# print test

# enc = gpg.encrypt_msg('A simple test of encryption with downloaded keys!', to)
# print enc

sign = gpg.sign_msg('A simple test of signing a message!')
print sign

gpg.verify_msg(sign)

# dec = gpg.decrypt_msg(enc, pw)
# print dec

# results, csrf = keybase.user_autocomplete('thor')
# for u in results:
#     print u['components']['username']['val']

# print "Sending encrypted email...."
# gmail.send_email('mtanous22@gmail.com', ['mtanous22@gmail.com', '<redacted>'], enc)
# print "Email away!"

# them = keybase.user_lookup('domain', 'christopherburg.com', 'pictures')
# pprint(them)

# keybase.edit_profile(name="Matt Tanous",
#                      bio="Anarchist working to develop a digital end-run around the state.",
#                      loc='United States')

# keys = keybase.key_fetch(me['public_keys']['primary']['kid'], ['encrypt'])
# pub_key = me['public_keys']['primary']['bundle']

# keybase.kill_sessions()

# gmail.auth()
