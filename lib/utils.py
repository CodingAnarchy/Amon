# General utility library
from re import match
import inspect


def comma_sep_list(lst):
    if not isinstance(lst, basestring):
        if len(lst) > 1:
            try:
                lst = ','.join(lst)[:-1]
            except TypeError:
                raise Exception(inspect.stack()[1][3] + "expects a comma separated string or list object.")
        else:
            lst = lst[0]
    elif not match(r'(\w+)?\w+', lst):
        raise Exception("User list not properly formatted: expected list or comma separated string")
    return lst