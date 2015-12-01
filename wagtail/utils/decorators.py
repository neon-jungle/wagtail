from __future__ import absolute_import, print_function, unicode_literals
from functools import wraps
from weakref import WeakKeyDictionary


def cached_classmethod(fn):
    """
    Cache the return value of a classmethod
    """

    # Use a WeakKeyDictionary incase the class is garbage collected.
    # EditHandlers make many, many classes which may or may not stay around.
    # This will avoid memory leaks
    cache = WeakKeyDictionary()

    @classmethod
    @wraps(fn)
    def method(cls):
        try:
            return cache[cls]
        except KeyError:
            value = cache[cls] = fn(cls)
            return value

    return method
