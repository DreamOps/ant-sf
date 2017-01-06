#!/usr/bin/python
"""Exchange prefix references in metadata files so that code can be deployed 
under a different namespace prefix. The search is brute-force, and this 
function expects prefixes to be sufficiently uncommon. 

Usage:
    % prefix_swap.py "/Users/thusted/git/example-org/src" "zPREFIX,PREFIX"

"""
"""
Use Case for prefix_swap.py

Motivation: Managed package releases cannot be rolled back (only rolled
forward). More flexibility is provided by developing against a test version of
the package under another prefix. When deploying from development to the domain
packaging org, the test prefix must be replaced with the domain prefix.

Stakeholders: Release Engineering

Output: Updated metadata files with the prefix substituted in place.

Prerequisite: The development metadata being updated is available locally
(checked out).

Postrequisite: The updated metadata is deployed to the domain packaging org.

Limitations:
1. If you try to roundtrip the prefixes (zPREFIX->PREFIX->zPREFIX), and check 
the Git status, a few cases may fail because the comments referred to a package 
prefix. (An exception that proves the rule!)

Caveats: 
1. The search is brute-force, and this script expects prefixes to be
sufficiently uncommon.
** Where XXX is the prefix, individual searches are conducted for "XXX__", 
   "XXX.", and "<namespace>XXX" -- where XXX is the prefix. If the prefix 
   were "ler", any reference to a "Handler." would also be changed. 
2. A package prefix should be consistently expressed in the same case used when
the prefix was registered in its Developer Edition org. Apex itself is case 
insensitive, but the API is sometimes case sensitive.   

Success Scenario:
1. External actor invokes script from command line passing sourcedir and 
prefix_swap arguments. 
2. Script evaluates arguments and passes source and target arguments to main.
3. Main validates the prefix_swap and sourcedir arguments, and controls the
process.
4. Process renames .object metadata files to reflect target prefix.
5. Process replaces the source prefix with the target prefix in all metadata
files under the source directory.
6. Process returns a tally of the modified files. 
** "{hits_tally} matches in {count} files"

Alternate Scenario:
(1a)
1. External actor sets environment properties "sourcedir" and "sf_prefix_swap".

(2a)
1. Script detects missing arguments and prints help message. 
** "Requires sourcedir, sf_prefix_swap as parameters or system properties."

(3a) 
1. Script detects invalid arguments and prints help message. 
** "Invalid source directory. Expecting: /.../example-org/src"
** "Exactly two prefixes are required: X1,X2"
"""
from os import environ, listdir, rename
from sys import argv

from tools_io import find_files, replace


def __rename_objects(directory, p1, p2):
    """Renames object files under sourcedir with the updated prefix.
    Modified files are saved in place. The number of files renamed
    is not reflected by the tally returned by main.
    """
    x1, x2 = (p1 + '__', p2 + '__')
    xlen = len(x1)
    path = directory + '/objects/'
    for fileName in listdir(path):
        if x1 == fileName[0:xlen]:
            rename(path + fileName, path + fileName.replace(x1, x2))


def main_verify_args(sourcedir, prefix_swap):
    if sourcedir is None or prefix_swap is None:
        raise ValueError("Both parameters are required: sourcedir, prefix_swap")

    if 'src' != sourcedir[-3:]:
        raise ValueError("Invalid source directory. "
                         "Expecting: /.../example-org/src")

    prefix = [x.strip() for x in prefix_swap.split(',')]
    if len(prefix) != 2:
        raise ValueError("Exactly two prefixes are required: X1,X2")

    return prefix


def main_find_files(sourcedir, replacements):
    (count, hits_tally, hits) = (0, 0, 0)
    for filename in find_files(sourcedir, '*'):
        hits = replace(filename, replacements)
        if hits:
            count += 1
            hits_tally += hits
    print("{hits_tally} matches in {count} files".format(
        hits_tally=hits_tally, count=count))



def main(sourcedir, prefix_swap):
    """Walks through files under the sourcedir, and tries the set of
    replacements for each file. Modified files are saved in place.
    The tally of matches and modified files is returned.

    Usage:
        sourcedir = '/Users/thusted/git/example-org/src'
        prefix_swap = 'zPREFIX,PREFIX'
        main(sourcedir,prefix_swap)
    """
    prefix = main_verify_args(sourcedir, prefix_swap)

    (p1, p2) = (prefix[0], prefix[1])

    __rename_objects(sourcedir, p1, p2)

    replacements = {p1 + '__': p2 + '__', p1 + '.': p2 + '.',
                    '<namespace>' + p1: '<namespace>' + p2}

    main_find_files(sourcedir, replacements)


if __name__ == '__main__':
    if len(argv) == 3:
        main(argv[1], argv[2])
    else:
        sf_sourcedir = None
        sf_prefix_swap = None
        try:
            sf_sourcedir = environ['sf_sourcedir']
            sf_prefix_swap = environ['sf_prefix_swap']
        except KeyError:
            print "Requires sf_sourcedir, sf_prefix_swap as parameters or system " \
                  "properties."
            exit(1)

        main(sf_sourcedir, sf_prefix_swap)
