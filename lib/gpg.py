# GPG utility library
from os import system

import gnupg


# clean GPG test directory on startup before proceeding with test
system('rm -rf /home/testgpguser/gpghome')
gpg = gnupg.GPG(gnupghome='/home/testgpguser/gpghome')


def gen_key(**kwargs):
    """ Generate new GPG key with possible parameters:
    key_type (default "RSA")
    key_length (default 1024)
    name_real (real name - default "Autogenerated Key")
    name_comment (default "Generated by gnupg.py")
    name_email (default <username>@<hostname>)
    expire_date (ISO date, number of days/weeks/monts/years, epoch value, or 0 for 'never')
    passphrase (default None)
    """
    print "Generating key..."
    name = "default user"
    email = "default email"
    if 'name_real' in kwargs:
        name = kwargs['name_real']
    if 'name_email' in kwargs:
        email = kwargs['name_email']

    input_data = gpg.gen_key_input(**kwargs)
    new_key = gpg.gen_key(input_data)
    print "Key generated for " + name + " with " + email
    return new_key


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


def export_keys(keys, sec=False):
    """ Export GPG keys with given key ids
    sec parameter indicates whether to export private keys
    """
    if not isinstance(sec, bool):
        raise TypeError("export_keys 'secret' parameter must be a boolean")
    aa_public_keys = gpg.export_keys(keys, sec)
    return aa_public_keys


def list_keys(sec=False):
    if not isinstance(sec, bool):
        raise TypeError("list_keys 'secret' parameter must be a boolean")
    return gpg.list_keys()


def encrypt_msg(msg, to):
    print "Encrypting message..."
    enc_str = None
    if isinstance(msg, file):
        with msg:
            # TODO: put output file in same path as input file
            status = gpg.encrypt_file(msg, recipients=to, always_trust=True, output='enc_msg.gpg')
            if not status.ok:
                raise Exception("GPG encryption error: \nstatus: " + status.status + '\nstderr: ' + status.stderr)
            with open('enc_msg.gpg', 'rb') as enc:
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
        msg = gpg.decrypt_file(enc, passphrase=pw, always_trust=True, output='dec_msg.txt')
    else:
        # treat enc as encrypted string
        msg = gpg.decrypt(enc, passphrase=pw, always_trust=True)
    if not msg.ok:
        raise Exception("GPG decryption error: \nstatus: " + msg.status + '\nstderr: ' + msg.stderr)
    return msg.data


def sign_msg(msg, keyid=None, detach=False, output=None):
    signed = gpg.sign(msg, keyid=keyid, detach=detach, output=output)
    return str(signed)


def verify_msg(msg):
    verified = gpg.verify(msg)
    if not verified:
        raise ValueError("Signature could not be verified!")
    print "Signature verified!"


def delete_keys(key):
    fp = key.fingerprint
    print "Deleting key with fingerprint " + fp
    if str(gpg.delete_keys(fp)) == 'Must delete secret key first':
        status = gpg.delete_keys(fp, True)
        if str(status) != 'ok':
            raise Exception("Deleting secret key " + fp + " failed.")
        status = gpg.delete_keys(fp)
        if str(status) != 'ok':
            raise Exception("Deleting public key " + fp + " failed.")
    print "Key with fingerprint " + fp + " deleted successfully."