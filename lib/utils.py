# General utility library
from re import match
import inspect
import sys
import ctypes
import logging

logger = logging.getLogger(__name__)


def comma_sep_list(input_lst):
    """Set up string or list to URL list parameter format"""
    if not isinstance(input_lst, basestring):
        # Convert list to proper format for URL parameters
        if len(input_lst) > 1:
            try:
                lst = ','.join(input_lst)
            except TypeError:
                raise Exception(inspect.stack()[1][3] + "expects a comma separated string or list object.")
        else:
            lst = input_lst[0]
    # Verify that strings passed in have the appropriate format (comma separated string)
    elif not match(r'(\w+,)?\w+', input_lst):
        raise Exception("User list not properly formatted: expected list or comma separated string")
    return lst


def build_list(comma_sep):
    lst = comma_sep.split(',')
    lst = [x.strip('_') for x in lst]
    print "List = " + str(lst)
    return lst


# Crashes program in OSX - resolve later
def zero_out(string):
    temp = "finding offset"
    header = ctypes.string_at(id(temp), sys.getsizeof(temp)).find(temp)

    loc = id(string) + header
    size = sys.getsizeof(string) - header

    logger.info("Clearing 0x%08x size %i bytes" % (loc, size))
    ctypes.memset(loc, 0, size)