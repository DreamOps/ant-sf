#!/usr/bin/python
"""Removes from a profile document the classAccesses elements that are not
enabled, and returns the pruned version to standard output.

To call from the Python CLI (with metadata present):
    ./profile_prune.py ~/8/"Custom Standard.profile" > pruned.profile

To call from the Ant CLI: ant -Dhome={} -Dsf_credentials={}
    -Dprofile_path_source=~/8/"Custom Standard.profile"

"""
"""
Use Case for profile_prune.py

Motivation: When a package has a good number of classes, the default
classAccesses elements bloat the document, making it more difficult to use
and review. The output of this script can be used with profile_package to
create a clean copy of an existing profile. The clean copy can also be modified
to use a different Salesforce license than the original.

Stakeholders: Release Engineering

Output: Well-formed profile document without redundant class access statements.

Prerequisite: Source profile is extracted and can be passed at command line.

Postrequisite: A prefix is injected into profiles being used with a managed
package.

Success Scenario:
1. External actor invokes script from command line passing source.profile
argument.
2. Script evaluates arguments and passes source arguments to main,
which orchestrates the process.
3. Process reads source into an lxml etree, pruning the tree to
remove elements that do not grant access.
4. Process returns well-formed profile XML document to standard output, with
default components removed.


"""
from os import environ
from sys import argv, exit

from tools_lxml import save_tree

from profile_delta import prune_tree


def main(profile_path_source, profile_path_target):
    """Reads profile from file system and renders pruned profile.
    """
    try:
        source_root = prune_tree(profile_path_source)
    except IOError:
        # Info error only. Not exception.
        print "{profile_path_source} is not available.".format(
            profile_path_source=profile_path_source)
        return 1
    save_tree(source_root, profile_path_target) 
    return 0


if __name__ == '__main__':
    if len(argv) == 3:
        main(argv[1], argv[2])
    else:
        profile_path_source = None
        profile_path_target = None
        try:
            profile_path_source = environ['profile_path_source']
            profile_path_target = environ['profile_path_target']
        except KeyError:
            print "Requires profile_path_source and profile_path_target as \
            parameters or system properties."
            exit(1)
        main(profile_path_source, profile_path_target)
