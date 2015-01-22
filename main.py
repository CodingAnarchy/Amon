from lib import keybase

lookup = 'temp'
users = []
fields = 'basics'
while lookup != '':
    lookup = raw_input("User to look up: ")
    users.append(lookup)

status = keybase.user_lookup(users, fields)

print status

user = raw_input("Username: ")
salt = keybase.get_salt(user)

pw = raw_input("Password: ")
status = keybase.login(user, pw, salt["salt"], salt["session"])

print status