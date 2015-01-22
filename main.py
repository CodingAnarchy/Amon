from lib import keybase

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

# Test code for logging in
# user = raw_input("Username: ")
# salt = keybase.get_salt(user)
#
# pw = raw_input("Password: ")
# status = keybase.login(user, pw, salt["salt"], salt["session"])
#
# print status

# Test code for obtaining a user's public key
pub_key = keybase.user_pub_key('thorodinson')
print pub_key