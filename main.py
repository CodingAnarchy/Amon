from lib import keybase

user = raw_input("Username: ")
salt = keybase.get_salt(user)

pw = raw_input("Password: ")
status = keybase.login(user, pw, salt["salt"], salt["session"])

print status