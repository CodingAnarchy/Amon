# Keybase API interface module
import json
from binascii import unhexlify
import hmac
from hashlib import sha512
from base64 import b64decode
import requests
import scrypt
from lib.utils import comma_sep_list
# import gnupg


kb_url = 'https://keybase.io/_/api/1.0/'


def get_salt(user):
    gs_url = kb_url + 'getsalt.json'
    r = requests.get(gs_url, params={'email_or_username': user})
    data = json.loads(r.text)
    if data["status"]["code"] != 0:
        raise Exception("Attempt to get salt from keybase returned error: " + str(data["status"]["name"]))
    result = {"salt": data["salt"], "session": data["login_session"]}
    return result


def login(user, pw, salt, session):
    print "Logging in..."
    login_url = kb_url + 'login.json'
    pwh = scrypt.hash(pw, unhexlify(salt), 2**15, 8, 1, 224)[192:224]
    hmac_pwh = hmac.new(pwh, b64decode(session), sha512)
    r = requests.post(login_url, params={'email_or_username': user, 'hmac_pwh': hmac_pwh.hexdigest(), 'login_session': session})
    data = json.loads(r.text)
    if data["status"]["code"] != 0:
        raise Exception("Attempt to login to keybase returned error: " + str(data["status"]["name"]))
    return data


def user_lookup(ltype, users, fields):
    ul_url = kb_url + 'user/lookup.json'

    # Verify type is valid lookup: github, twitter, and reddit (at least) may not work due to API-side issue - 1/22/2015
    if ltype not in ['usernames', 'domain', 'twitter', 'github', 'reddit', 'hackernews', 'coinbase', 'key_fingerprint']:
        raise Exception("User lookup attempted with invalid type of lookup.")
    elif len(users) > 1 and not ltype == 'usernames':
        raise Exception('Only username lookups can be multi-valued.')

    # Verify user and fields lists are in an appropriate type and format
    users = comma_sep_list(users)
    fields = comma_sep_list(fields)

    r = requests.get(ul_url, params={ltype: users, 'fields': fields})
    data = json.loads(r.text)
    if data["status"]["code"] != 0:
        raise Exception("Attempt to lookup users from keybase returned error: " + str(data["status"]["name"]))
    return data


def user_pub_key(user):
    print "Obtaining public key for " + user
    uk_url = 'https://keybase.io/' + user + '/key.asc'
    r = requests.get(uk_url)
    if r.text == "404":
        raise Exception("User's public key could not be found on keybase.")
    return r.text


def key_fetch(key_ids, ops=None, session=None):
    print "Fetching keys..."
    kf_url = kb_url + 'key/fetch.json'
    key_ids = comma_sep_list(key_ids)
    opt = 0x00
    if ops is not None:
        if not set(ops) < {'encrypt', 'decrypt', 'verify', 'sign'}:
            raise Exception("Invalid operation for key fetch selected.")
        if 'encrypt' in ops:
            opt |= 0x01
        if 'decrypt' in ops:
            opt |= 0x02
        if 'verify' in ops:
            opt |= 0x04
        if 'sign' in ops:
            opt |= 0x08

        if 'decrypt' in ops or 'sign' in ops:
            if session is None:
                raise Exception("Retrieving private key for encrypting or signing requires login session.")
            r = requests.get(kf_url, params={'kids': key_ids, 'ops': opt, 'login_session': session})
        else:
            r = requests.get(kf_url, params={'kids': key_ids, 'ops': opt})

    data = json.loads(r.text)
    if data["status"]["code"] != 0:
        raise Exception("Attempt to fetch keys error: " + str(data["status"]["name"]) + '\nDescription: ' +
                        str(data["status"]["desc"]))
    return data['keys']
