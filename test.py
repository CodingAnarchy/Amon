import sys
from gui.gtk import Amon


# keys, csrf = amon.key_fetch(me['private_keys']['primary']['kid'], ['sign'], session)

# Test code for obtaining a user's public key
# pub_key = amon.user_pub_key('christopherburg')
# import_result = gpg.import_keys(pub_key)
# pprint(import_result.results)

# print gpg.list_keys(True)

# test = gpg.export_keys(to)
# print test

# enc = gpg.encrypt_msg('A simple test of encryption with downloaded keys!', to)
# print enc

# sign = gpg.sign_msg('A simple test of signing a message!')
# print sign
#
# gpg.verify_msg(sign)

# dec = gpg.decrypt_msg(enc, pw)
# print dec

# results = amon.user_autocomplete('thor')
# for u in results:
#     print u['components']['username']['val']

# print "Sending encrypted email...."
# gmail.send_email('mtanous22@gmail.com', ['mtanous22@gmail.com', '<redacted>'], enc)
# print "Email away!"

# them = amon.user_lookup('domain', 'christopherburg.com', 'pictures')
# pprint(them)

# amon.edit_profile(name="Matt Tanous",
#                      bio="Anarchist working to develop a digital end-run around the state.",
#                      loc='United States')

# amon.kill_sessions()

# gmail.auth()

app = Amon()
exit_status = app.run()
sys.exit(exit_status)
