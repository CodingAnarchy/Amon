# Keybase API interface module
import json
from binascii import unhexlify
import hmac
from hashlib import sha512
import msgpack
from base64 import b64decode
import requests
import scrypt
from .utils import comma_sep_list
from pprint import pprint
from collections import namedtuple

kb_url = 'https://keybase.io/_/api/1.0/'
Session = namedtuple('session', 'session_id csrf_token')
session = ''


def get_salt(user):
    gs_url = kb_url + 'getsalt.json'
    r = requests.get(gs_url, params={'email_or_username': user})
    data = json.loads(r.text)
    if data["status"]["code"] != 0:
        raise Exception("Attempt to get salt error: " + str(data["status"]["name"]) +
                        '\nDescription: ' + str(data["status"]["desc"]))
    return data["salt"], data["login_session"]


def login(user, pw):
    print "Logging in..."
    global session
    salt, session_id = get_salt(user)
    login_url = kb_url + 'login.json'
    pwh = scrypt.hash(pw, unhexlify(salt), 2**15, 8, 1, 224)[192:224]
    hmac_pwh = hmac.new(pwh, b64decode(session_id), sha512)
    r = requests.post(login_url, params={'email_or_username': user, 'hmac_pwh': hmac_pwh.hexdigest(),
                                         'login_session': session_id})
    data = json.loads(r.text)
    if data["status"]["code"] != 0:
        raise Exception("Login attempt error: " + str(data["status"]["name"]) + '\nDescription: ' +
                        str(data["status"]["desc"]))
    print "Logged in!"
    session = Session(session_id, data['csrf_token'])
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
        raise Exception("Attempt to lookup users error: " + str(data["status"]["name"]) + '\nDescription: ' +
                        str(data["status"]["desc"]))
    return data


def user_autocomplete(user):
    ua_url = kb_url + 'user/autocomplete.json'
    r = requests.get(ua_url, params={'q': user})
    data = json.loads(r.text)
    if data["status"]["code"] != 0:
        raise Exception("Attempt to autocomplete user query error: " + str(data["status"]["name"]) +
                        '\nDescription: ' + str(data["status"]["desc"]))
    return data['completions'], data['csrf_token']


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
            r = requests.get(kf_url, params={'kids': key_ids, 'ops': opt, 'session': session})
        else:
            r = requests.get(kf_url, params={'kids': key_ids, 'ops': opt})

    data = json.loads(r.text)
    if data["status"]["code"] != 0:
        raise Exception("Attempt to fetch keys error: " + str(data["status"]["name"]) + '\nDescription: ' +
                        str(data["status"]["desc"]))
    return data['keys'], data['csrf_token']


def decode_priv_key(obj, ts):
    # Private keys are encoded on Keybase using P3SKB format and TripleSec
    # Have to decode any private keys obtained before using them with GPG
    enc = msgpack.unpackb(b64decode(obj))
    priv = enc['body']['priv']['data']
    priv_key = ts.decrypt(priv)
    return priv_key


# In progress - does not currently work!  Will be necessary for upload of private key to keybase (if desired).
# def encode_keys(pub, sec, ts):
#     # Private keys are encoded on Keybase using P3SKB format and TripleSec
#     # Have to encode any private keys before uploading them
#     enc = ts.encrypt(sec)
#     version = 1
#     encrypt = 3  # TripleSec version 3
#     tag = 513
#     hash_type = 8  # corresponds to SHA-256
#     hash_val = buffer(0)
#
#     obj = json.dumps({'version': version, 'tag': tag, 'hash': {'type': hash_type, 'value': hash_val},
#                      'body': {'pub': pub, 'priv': {'data': enc, 'encryption': encrypt}}})
#     pprint(obj)
#     # enc = msgpack.unpackb(b64decode(obj))
#     # enc = enc['body']['priv']['data']
#     return obj


def kill_sessions(session, csrf):
    ks_url = kb_url + 'session/killall.json'
    # print csrf
    r = requests.post(ks_url, data={'session': session, 'csrf_token': csrf})
    data = json.loads(r.text)
    if data['status']['code'] != 0:
        raise Exception("Attempt to kill user login sessions error: " + str(data["status"]["name"]) +
                        '\nDescription: ' + str(data["status"]["desc"]))
    return


def edit_profile(session, csrf, bio=None, loc=None, name=None):
    ep_url = kb_url + 'profile-edit.json'
    params = {}
    if bio is not None:
        params['bio'] = bio
    if name is not None:
        params['full_name'] = name
    if loc is not None:
        params['location'] = loc
    if not params:
        raise Exception("Editing keybase profile requires at least one parameter: name, bio, or location.")
    params['csrf_token'] = csrf
    params['session'] = session
    r = requests.post(ep_url, data=params)
    data = json.loads(r.text)
    if data['status']['code'] != 0:
        raise Exception("Attempt to edit keybase profile error: " + str(data["status"]["name"]) +
                        '\nDescription: ' + str(data["status"]["desc"]))
    return data['csrf_token']


def discover_users(lookups, usernames_only=False, flatten=False):
    kd_url = kb_url + 'user/discover.json'
    if not isinstance(lookups, dict):
        raise Exception()
    for t in lookups:
        # Verify the selected type will work with keybase API call
        if t not in ['twitter', 'github', 'hackernews', 'web', 'coinbase', 'key_fingerprint']:
            raise Exception("Keybase discover users error: cannot discover users using type " + t + ".")
        # Convert lookups to necessary format for API call
        lookups[t] = comma_sep_list(lookups[t])

    # Set up parameter call for request
    params = lookups
    if usernames_only:
        params['usernames_only'] = 1
    if flatten:
        params['flatten'] = 1

    r = requests.get(kd_url, params=params)
    data = json.loads(r.text)
    if data["status"]["code"] != 0:
        raise Exception("Attempt to discover users error: " + str(data["status"]["name"]) + '\nDescription: ' +
                        str(data["status"]["desc"]))
    return data
