# GPG utility library
from os import system

import gnupg


# clean GPG test directory on startup before proceeding with test
system('rm -rf /home/testgpguser/gpghome')
gpg = gnupg.GPG(gnupghome='/home/testgpguser/gpghome')


def import_keys(keys):
    print "Importing keys..."
    result = None
    if isinstance(keys, basestring):
        result = gpg.import_keys(keys)
    elif isinstance(keys, list):
        for k in keys:
            result = gpg.import_keys(k)
    elif isinstance(keys, file):
        key_data = keys.read()
        result = gpg.import_keys(key_data)
    return result


def export_keys(keys):
    aa_public_keys = gpg.export_keys(keys)
    return aa_public_keys


def list_keys(secret=False):
    if not isinstance(secret, bool):
        raise Exception("list_keys 'secret' parameter must be a boolean")
    return gpg.list_keys()


def encrypt_msg(msg, to):
    print "Encrypting msg..."
    enc_str = None
    if isinstance(msg, file):
        with msg:
            # TODO: put output file in same path as input file
            status = gpg.encrypt_file(msg, recipients=to, always_trust=True, output='enc_msg.txt')
            if not status.ok:
                raise Exception("GPG encryption error: \nstatus: " + status.status + '\nstderr: ' + status.stderr)
            with open('enc_msg.txt', 'rb') as enc:
                enc_str = enc.read()
                # TODO: Query user for deletion of original and/or encrypted file, if desired
    else:
        # treat msg as plaintext string
        enc_data = gpg.encrypt(msg, to, always_trust=True)
        enc_str = str(enc_data)
        if not enc_str.ok:
            raise Exception("GPG encryption error: \nstatus: " + enc_str.status + '\nstderr: ' + enc_str.stderr)
    if enc_str is None:
        raise Exception("GPG encryption failed to encrypt a message.")
    return enc_str


def decrypt_msg(enc, pw):
    print "Decrypting message..."
    if isinstance(enc, file):
        # TODO: Decrypt file path
        return None
    else:
        # treat enc as encrypted string
        msg = gpg.decrypt(enc, passphrase=pw, always_trust=True)
        if not msg.ok:
            raise Exception("GPG decryption error: \nstatus: " + msg.status + '\nstderr: ' + msg.stderr)
        return msg.data

