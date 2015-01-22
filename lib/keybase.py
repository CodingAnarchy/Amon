# Keybase API interface module
import json
from binascii import unhexlify
import hmac
from hashlib import sha512
from base64 import b64decode

import requests
import scrypt


kb_url = 'https://keybase.io/_/api/1.0/'


def get_salt(user):
    gs_url = kb_url + 'getsalt.json'
    r = requests.get(gs_url, params={'email_or_username': user})
    data = json.loads(r.text)
    if data["status"]["code"] != 0:
        raise Exception("Attempt to get salt from keybase returned error code: " + str(data["status"]["code"]))
    result = {"salt": data["salt"], "session": data["login_session"]}
    return result


def login(user, pw, salt, session):
    login_url = kb_url + 'login.json'
    pwh = scrypt.hash(pw, unhexlify(salt), 2**15, 8, 1, 224)[192:224]
    hmac_pwh = hmac.new(pwh, b64decode(session), sha512)
    r = requests.post(login_url, params={'email_or_username': user, 'hmac_pwh': hmac_pwh.hexdigest(), 'login_session': session})
    data = json.loads(r.text)
    if data["status"]["code"] != 0:
        raise Exception("Attempt to login to keybase returned error code: " + str(data["status"]["code"]))
    return data


def user_lookup(users):
    ul_url = kb.url + 'user/lookup.json'