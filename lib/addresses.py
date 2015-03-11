import logging
import warnings
try:
    import cPickle as pickle
except ImportError:
    import pickle
from lib.error import AddressBookError

logger = logging.getLogger(__name__)


class AddressBook:
    def __init__(self, name=None):
        self.name = name

        try:
            self.contact_list = pickle.load(open(self.name + '_address_book.p', 'rb'))
        except IOError:
            logger.debug('Could not load ' + self.name + ' address book!')
            warnings.warn('Could not load ' + self.name + ' address book!')
            self.contact_list = {}

    def add_contact(self, name, email, fingerprint, primary=True):
        if primary:
            self.contact_list[name]['primary'] = [email, fingerprint]
        else:
            self.contact_list[name]['alts'].append([email, fingerprint])
        pickle.dump(self.contact_list, open(self.name + '_address_book.p', 'wb'))

    def del_contact(self, name, email):
        if self.contact_list[name]['primary'][0] == email:
            del self.contact_list[name]
        else:
            try:
                idx = zip(*self.contact_list[name]['alts'])[0].index(email)
                del self.contact_list[name]['alts'][idx]
            except ValueError:
                raise AddressBookError("Could not find email address to delete!")
        pickle.dump(self.contact_list, open(self.name + '_address_book.p', 'wb'))