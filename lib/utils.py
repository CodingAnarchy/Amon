# General utility library
from re import match
import inspect


def comma_sep_list(lst):
    """Set up string or list to URL list parameter format"""
    if not isinstance(lst, basestring):
        # Convert list to proper format for URL parameters
        if len(lst) > 1:
            try:
                lst = ','.join(lst)[:-1]
            except TypeError:
                raise Exception(inspect.stack()[1][3] + "expects a comma separated string or list object.")
        else:
            lst = lst[0]
    # Verify that strings passed in have the appropriate format (comma separated string)
    elif not match(r'(\w+,)?\w+', lst):
        raise Exception("User list not properly formatted: expected list or comma separated string")
    return lst