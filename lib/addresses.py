import logging
import warnings
try:
    import cPickle as pickle
except ImportError:
    import pickle
from lib.error import AddressBookError

logger = logging.getLogger(__name__)


class AddressBook:
    def __init__(self, name='primary'):
        self.name = name

        try:
            self.contact_list = pickle.load(open(self.name + '_address_book.p', 'rb'))
        except IOError:
            logger.debug('Could not load ' + self.name + ' address book!')
            warnings.warn('Could not load ' + self.name + ' address book!')
            self.contact_list = {}

    def add_contact(self, name, email, fingerprint, primary=True):
        # Make sure name is in contact list to prevent key error
        if name not in self.contact_list:
            self.contact_list[name] = {}

        if primary:
            self.contact_list[name]['primary'] = (email, fingerprint)
        else:
            if 'alts' not in self.contact_list[name]:
                self.contact_list[name]['alts'] = []
            self.contact_list[name]['alts'].append((email, fingerprint))
        pickle.dump(self.contact_list, open(self.name + '_address_book.p', 'wb'))

    def get_contact_key(self, name, primary=True, alt_email=None):
        if not primary and alt_email is None:
            raise AddressBookError('Getting a non-primary key fingerprint requires an alternate email.')
        if primary:
            key = self.contact_list[name]['primary'][1]
        else:
            key = next((v[1] for v in self.contact_list[name]['alts'] if v[0] == alt_email), None)

        if key is None:
            warnings.warn('Contact not found in address book - returning None.', RuntimeWarning)
        return key

    def get_contact_email(self, name, primary=True, alt_idx=None):
        if not primary and alt_idx is None:
            raise AddressBookError('Getting a non-primary email requires an alternate index.')

        if primary:
            email = self.contact_list[name]['primary'][0]
        else:
            email = self.contact_list[name]['alts'][alt_idx][0]
        return email

    def del_contact(self, name, email=None):
        if email is None:
            del self.contact_list[name]
        elif self.contact_list[name]['primary'][0] == email:
            del self.contact_list[name]['primary']
        else:
            try:
                idx = next((i for i, v in enumerate(self.contact_list[name]['alts']) if v[0] == email), None)
                del self.contact_list[name]['alts'][idx]
            except ValueError:
                raise AddressBookError("Could not find email address to delete!")
        pickle.dump(self.contact_list, open(self.name + '_address_book.p', 'wb'))