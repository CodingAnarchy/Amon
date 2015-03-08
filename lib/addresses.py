import logging
import warnings
try:
    import cPickle as pickle
except ImportError:
    import pickle

logger = logging.getLogger(__name__)

try:
    address_book = pickle.load(open('address_book.p', 'rb'))
except IOError:
    logger.debug('Could not load address book!')
    warnings.warn('Could not load address book!')
    address_book = []


def add_contact(name, email, fingerprint):
    address_book.append({'name': name, 'email': email, 'key': fingerprint})
    pickle.dump(address_book, open('address_book.p', 'wb'))
