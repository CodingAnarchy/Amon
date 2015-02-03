# Keybase API interface module
import json
from binascii import unhexlify
import hmac
from hashlib import sha512
from base64 import b64decode
from os import urandom

import msgpack
import requests
import scrypt
import triplesec

from .utils import comma_sep_list
from error import *

# from pprint import pprint
from collections import namedtuple
from warnings import warn

kb_url = 'https://keybase.io/_/api/1.0/'
Session = namedtuple('session', 'id csrf')


# Currently requires invitation id - don't use yet
def signup(name, email, uname, pw, invite):
    su_url = kb_url + 'signup.json'
    salt = hex(urandom(16))
    pwh = scrypt.hash(pw, unhexlify(salt), 2**15, 8, 1, 224)  # Verify these parameters are appropriate?
    r = requests.post(su_url, data={'name': name, 'email': email, 'username': uname,
                                    'pwh': pwh, 'salt': salt, 'invitation_id': invite})
    data = json.loads(r.text)
    # TODO: parse the signup return for reuse of username/email instead of just failing
    if data['status']['code'] != 0:
        raise KeybaseError("Sign up failed: " + str(data['status']['name']) +
                           '\nDescription: ' + str(data["status"]["desc"]))
    return


# Look up users on Keybase.io
def user_lookup(ltype, users, fields):
    ul_url = kb_url + 'user/lookup.json'

    # Coerce string type inputs to items in list
    if isinstance(users, basestring):
        users = users.split(',')
    if isinstance(fields, basestring):
        fields = fields.split(',')

    # Verify type is valid lookup: github, twitter, and reddit (at least)
    # may not work due to API server-side issue - 1/22/2015
    if ltype not in ['usernames', 'domain', 'twitter', 'github', 'reddit', 'hackernews', 'coinbase', 'key_fingerprint']:
        raise Exception("User lookup attempted with invalid type of lookup.")
    elif len(users) > 1 and not ltype == 'usernames':
        raise Exception('Only username lookups can be multi-valued.')

    if not set(fields).issubset({'pictures', 'basics', 'public_keys', 'profile', 'proofs_summary',
                                 'remote_key_proofs', 'sigs', 'cryptocurrency_addresses'}):
        raise Exception("Invalid fields for user lookup.")

    # Verify user and fields lists are in an appropriate type and format for URL call
    users = comma_sep_list(users)
    fields = comma_sep_list(fields)

    r = requests.get(ul_url, params={ltype: users, 'fields': fields})
    data = json.loads(r.text)
    if data["status"]["code"] != 0:
        raise KeybaseError("Attempt to lookup users error: " + str(data["status"]["name"]) +
                           '\nDescription: ' + str(data["status"]["desc"]))
    return data['them']


def user_autocomplete(user):
    ua_url = kb_url + 'user/autocomplete.json'
    r = requests.get(ua_url, params={'q': user})
    data = json.loads(r.text)
    if data["status"]["code"] != 0:
        raise KeybaseError("Attempt to autocomplete user query error: " + str(data["status"]["name"]) +
                           '\nDescription: ' + str(data["status"]["desc"]))
    return data['completions']


def user_pub_key(user):
    print "Obtaining public key for " + user
    uk_url = 'https://keybase.io/' + user + '/key.asc'
    r = requests.get(uk_url)
    if r.text == "404":
        raise KeybaseError("User's public key could not be found on keybase.")
    return r.text


def key_fetch(key_ids, ops=None):
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
            if session.id is None:
                raise Exception("Retrieving private key for encrypting or signing requires login session.")
            r = requests.get(kf_url, params={'kids': key_ids, 'ops': opt, 'session': session.id})
        else:
            if session.id is None:
                warn("Session should be submitted when fetching keys for CSRF verification!", CSRFWarning)
                r = requests.get(kf_url, params={'kids': key_ids, 'ops': opt})
            else:
                r = requests.get(kf_url, params={'kids': key_ids, 'ops': opt, 'session': session.id})
    else:
        warn("Generally want to select operations needed for fetched keys to ensure future usability.", RuntimeWarning)
        if session.id is None:
            warn("Session should be submitted when fetching keys for CSRF verification!", CSRFWarning)
            r = requests.get(kf_url, params={'kids': key_ids})
        else:
            r = requests.get(kf_url, params={'kids': key_ids, 'session': session.id})

    data = json.loads(r.text)
    if data["status"]["code"] != 0:
        raise KeybaseError("Attempt to fetch keys error: " + str(data["status"]["name"]) +
                           '\nDescription: ' + str(data["status"]["desc"]))
    if session.id is not None and data['csrf_token'] != session.csrf:
        raise CSRFError(session.csrf, data['csrf_token'])
    return data['keys']


def decode_priv_key(obj, ts):
    # Private keys are encoded on Keybase using P3SKB format and TripleSec
    # Have to decode any private keys obtained before using them with GPG
    enc = msgpack.unpackb(b64decode(obj))
    priv = enc['body']['priv']['data']
    priv_key = ts.decrypt(priv)
    return priv_key


# In progress - does not currently work!  Will be necessary for upload of private key to amon (if desired).
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

def edit_profile(bio=None, loc=None, name=None):
    print "Updating profile..."
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
    params['csrf_token'] = session.csrf
    params['session'] = session.id
    r = requests.post(ep_url, data=params)
    data = json.loads(r.text)
    if data['status']['code'] != 0:
        raise KeybaseError("Attempt to edit keybase profile error: " + str(data["status"]["name"]) +
                           '\nDescription: ' + str(data["status"]["desc"]))
    if data['csrf_token'] != session.csrf:
        raise CSRFError(session.csrf, data['csrf_token'])
    return


def discover_users(lookups, usernames_only=False, flatten=False):
    kd_url = kb_url + 'user/discover.json'
    if not isinstance(lookups, dict):
        raise Exception("Discovering users requires a dictionary of types => user ids.")
    for t in lookups:
        # Verify the selected type will work with amon API call
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
        raise KeybaseError("Attempt to discover users error: " + str(data["status"]["name"]) +
                           '\nDescription: ' + str(data["status"]["desc"]))
    return data


def kill_sessions():
    ks_url = kb_url + 'session/killall.json'
    r = requests.post(ks_url, data={'session': session.id, 'csrf_token': session.csrf})
    data = json.loads(r.text)
    if data['status']['code'] != 0:
        raise KeybaseError("Attempt to kill user login sessions error: " + str(data["status"]["name"]) +
                           '\nDescription: ' + str(data["status"]["desc"]))
    return


class KeybaseUser:
    def __init__(self):
        self.ts = None
        self.pub_key = None
        self.enc_sec_key = None
        self.session = None

    def get_pub_key(self):
        return self.pub_key

    def get_sec_key(self):
        return decode_priv_key(self.enc_sec_key, self.ts)

    def get_salt(self, user):
        gs_url = kb_url + 'getsalt.json'
        r = requests.get(gs_url, params={'email_or_username': user})
        data = json.loads(r.text)
        if data["status"]["code"] != 0:
            raise KeybaseError("Attempt to get salt error: " + str(data["status"]["name"]) +
                               '\nDescription: ' + str(data["status"]["desc"]))
        return data["salt"], data["login_session"]

    def login(self, user, pw):
        # print "Logging in..."
        salt, session_id = self.get_salt(user)
        login_url = kb_url + 'login.json'
        pwh = scrypt.hash(pw, unhexlify(salt), 2**15, 8, 1, 224)[192:224]
        hmac_pwh = hmac.new(pwh, b64decode(session_id), sha512)
        r = requests.post(login_url, data={'email_or_username': user, 'hmac_pwh': hmac_pwh.hexdigest(),
                                           'login_session': session_id})
        data = json.loads(r.text)
        if data["status"]["code"] != 0:
            if str(data["status"]["name"]) in ["BAD_LOGIN_PASSWORD", "BAD_LOGIN_USER_NOT_FOUND"]:
                raise LoginError("Incorrect login information: " + str(data["status"]["desc"]) + '!')
            raise KeybaseError("Login attempt error: " + str(data["status"]["name"]) +
                               '\nDescription: ' + str(data["status"]["desc"]))
        # print "Logged in!"
        self.session = Session(data['session'], data['csrf_token'])
        return data['me']