#!/usr/bin/python
"""Centralize IO utilities used by multiple modules.
"""

from fnmatch import fnmatch
from os import path, walk

def find_files(directory, pattern):
    """Yields filenames matching a pattern in a directory (generic). 
    This function is a generator that can be used in a for loop. 

    >>> for filename in find_files('.','tools_io.py'):
    ...     print filename
    ... 
    ./tools_io.py
    """
    for root, dirs, files in walk(directory):
        for basename in files:
            if fnmatch(basename, pattern):
                filename = path.join(root, basename)
                yield filename


def replace(filename, replacements):
    """Applies any number of substitutions in the replacements map to the file
    referenced by filename. Any modified file is written back, and the
    original file overwritten. The number of lines modified is returned.
    """
    zero = 0
    try:
        alpha = open(filename).read()
    except IOError:
        return zero
    hits = 0
    for key in replacements.keys():
        count = alpha.count(key)
        if count>0:
            alpha = alpha.replace(key, replacements[key])
            hits += count
    if hits>0:
        try:
            omega = open(filename, 'w')
            omega.write(alpha)
            omega.close()
        except IOError:
            return zero
        return hits
    else:
        return zero

