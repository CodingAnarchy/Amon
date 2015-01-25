# GPG utility library
import gnupg
from os import system

# clean GPG test directory on startup before proceeding with test
system('rm -rf /home/testgpguser/gpghome')
gpg = gnupg.GPG(gnupghome='/home/testgpguser/gpghome')


def import_keys(keys):
    print "Importing keys..."
    if isinstance(keys, basestring):
        result = gpg.import_keys(keys)
    elif isinstance(keys, list):
        for k in keys:
            result = gpg.import_keys(k)
    elif isinstance(keys, file):
        key_data = open(keys).read()
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
    if isinstance(msg, file):
        # TODO: Encrypt file path
        return None
    else:
        # treat msg as plaintext string
        enc_data = gpg.encrypt(msg, to, always_trust=True)
        enc_str = str(enc_data)
        if not enc_str.ok:
            raise Exception("GPG encryption error: \nstatus: " + enc_str.status + '\nstderr: ' + enc_str.stderr)
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

