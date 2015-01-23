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
    print aa_public_keys
    return


def encrypt_msg(msg, to):
    if isinstance(msg, file):
        # TODO: Encrypt file path
        return None
    else:
        # treat msg as string
        enc_data = gpg.encrypt(msg, to + '@keybase.io')
        enc_str = str(enc_data)
        print 'ok :', enc_data.ok
        print 'status: ', enc_data.status
        print 'stderr: ', enc_data.stderr
        print 'message: ', msg
        print 'enc: ', enc_str
        return enc_str


