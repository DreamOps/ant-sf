#!/usr/bin/python
"""Compare a source and target profile and output a well-formed
target_upgrade.profile granting access to components available in
target that are not granted by source.

To call from the Python CLI (with metadata present): 
    ./profile_delta.py ~/8/"Custom Standard.profile"
                       ~/9/"Custom Standard.profile"
                       ~/"Custom Standard.profile"

To call from the Ant CLI: ant -Dhome={} -Dsf_credentials={} 
    -Dprofile_path_source=~/8/"Custom Standard.profile"
    -Dprofile_path_target=~/9/"Custom Standard.profile"
    -Dprofile_path_output=~/"Custom Standard.profile"

To run the embedded tests: python -m doctest -v profile_delta.py
"""
"""
Use Case for profile_delta.py

Motivation: Generates profile document to update existing standard profiles
with new components added as part of a major upgrade.

Stakeholders: Release Engineering

Output: Well-formed profile document granting access to components available in
target that are not granted by source.

Prerequisite: Source and target profiles are extracted and can be passed at
command line. Source is the profile with the lower version number.

Postrequisite: A prefix is injected into profiles being used with a managed
package.

Assumptions: 
1. Target is a superset of source. 
2. The access elements can be enumerated in a static data structure.
3. For a major version upgrade, we only need to specify the permissions that we
are adding and granting.

Success Scenario:
1. External actor invokes script from command line passing source.profile and
target.profile arguments.
2. Script evaluates arguments and passes source and target arguments to main,
which orchestrates the process.
3. Process reads source and target into lxml etrees, pruning each tree to
remove elements that do not grant access (and to release memory).
4. For each access element, process scans the target and source, and creates a
set of the element names, using a strategy specific to the access type.
5. Process returns an output set by iterating through target set to isolate
elements not present in the source set.
6. Working from the output set, subfunction finds element in target etree and
copies it to the output etree (creating the tree if it doesn't exist).
7. When all access elements are processed, process savers a well-formed profile
to a given path on the file system.

Alternate Scenario:

(1a)
1. External actor sets environment properties for the source and target
profiles.

(2a)
1. Script detects missing arguments and prints help message. 

(3a)
1. Each access element passes arguments to a utility function to determine
whether access is granted.

"""
"""
Sample Output

<?xml version="1.0" encoding="UTF-8"?>
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <applicationVisibilities>
        <application>MY_APPLICATION</application>
        <default>true</default>
        <visible>true</visible>
    </applicationVisibilities>
    <classAccesses>
        <apexClass>AccountHierarchyBuilder</apexClass>
        <enabled>true</enabled>
    </classAccesses>
    <fieldPermissions>
        <editable>true</editable>
        <field>AppealProductLink__c.AppealParameterName__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <layoutAssignments>
        <layout>AppealProductLink__c-Appeal Product Link Layout</layout>
    </layoutAssignments>
    <layoutAssignments>
        <layout>Account-Account Layout</layout>
        <recordType>Account.Business_Account</recordType>
    </layoutAssignments>
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>true</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>true</modifyAllRecords>
        <object>AppealProductLink__c</object>
        <viewAllRecords>true</viewAllRecords>
    </objectPermissions>
    <pageAccesses>
        <apexPage>OrderMerchandiseProducts</apexPage>
        <enabled>true</enabled>
    </pageAccesses>
    <tabVisibilities>
        <tab>AppealProductLink__c</tab>
        <visibility>DefaultOn</visibility>
    </tabVisibilities>
    <userPermissions>
        <enabled>true</enabled>
        <name>ViewSetup</name>
    </userPermissions>
</Profile>
"""
from copy import deepcopy
from os import environ
from sys import argv, exit

from lxml import etree

from tools_lxml import save_tree, sforce_root, SF_URI, namespace_declare, namespace_prepend


# ---- NOTE TO READER ----
# In Python, all functions must be declared before they are used.
# The best way to read the source is to start at the end with the
# main function, and step up.
# ----


# element_parent: [extract_fetch_child, prune_child] }
# "None" is a place-holder for not-applicable
PARENTS = {'applicationVisibilities': ['application', 'visible'],
           'classAccesses': ['apexClass', 'enabled'],
           'fieldPermissions': ['field', 'readable'],
           'layoutAssignments': ['layout', 'None'],
           'objectPermissions': ['object', 'allowRead'],
           'pageAccesses': ['apexPage', 'enabled'],
           'recordTypeVisibilities': ['recordType', 'visible'],
           'tabVisibilities': ['tab', 'visibility']}
EXTRACT_CHILD = 0
FETCH_CHILD = 0
PRUNE_CHILD = 1


def example_class_access_element(root, class_name, is_enabled):
    parent = etree.SubElement(root, 'classAccesses')
    child = etree.SubElement(parent, 'apexClass')
    child.text = class_name
    child2 = etree.SubElement(parent, 'enabled')
    child2.text = is_enabled
    return root


def example_profile_metadata_source():
    """Generates an example profile metadata document.

    >>> root = example_profile_metadata_source()
    >>> print_tree(root)
    <?xml version='1.0' encoding='UTF-8'?>
    <Profile xmlns="http://soap.sforce.com/2006/04/metadata">
      <classAccesses>
        <apexClass>ARTransactionsTest</apexClass>
        <enabled>false</enabled>
      </classAccesses>
      <classAccesses>
        <apexClass>AccountAddressManager</apexClass>
        <enabled>true</enabled>
      </classAccesses>
    </Profile>
    <BLANKLINE>
    """
    root = sforce_root('Profile')
    example_class_access_element(root, 'ARTransactionsTest', 'false')
    example_class_access_element(root, 'AccountAddressManager', 'true')
    return root


def example_profile_metadata_target():
    """Generates an example profile metadata document.

    >>> root = example_profile_metadata_target()
    >>> print_tree(root)
    <?xml version='1.0' encoding='UTF-8'?>
    <Profile xmlns="http://soap.sforce.com/2006/04/metadata">
      <classAccesses>
        <apexClass>ARTransactionsTest</apexClass>
        <enabled>false</enabled>
      </classAccesses>
      <classAccesses>
        <apexClass>AccountAddressManager</apexClass>
        <enabled>true</enabled>
      </classAccesses>
      <classAccesses>
        <apexClass>AccountHierarchyBuilder</apexClass>
        <enabled>true</enabled>
      </classAccesses>
      <classAccesses>
        <apexClass>TransactionTestData</apexClass>
        <enabled>false</enabled>
      </classAccesses>
    </Profile>
    <BLANKLINE>
    """
    root = example_profile_metadata_source()
    example_class_access_element(root, 'AccountHierarchyBuilder', 'true')
    example_class_access_element(root, 'TransactionTestData', 'false')
    return root


class FindElements:
    """Implements a template strategy for use with various actions, such as
    extract, fetch, and prune. Each action creates it own subclass and
    overrides do_yield and do_return.
    """
    my_source = None
    my_target = None
    my_names = None
    my_test_mode = False

    def __init__(self):
        pass

    def do_yield(self, parent, child_text):
        raise NotImplementedError()

    def do_return(self):
        raise NotImplementedError()

    def do(self, source, target, parent_name, child_name, names):
        self.my_source = source
        self.my_target = target
        self.my_names = names
        ns = namespace_declare(self.my_test_mode)
        parent_name_match = namespace_prepend(parent_name, self.my_test_mode)
        pv = self.my_source.findall(parent_name_match, ns)
        child_name_match = namespace_prepend(child_name, self.my_test_mode)
        for parent in pv:
            child = parent.find(child_name_match, ns)
            if child is not None and child.text is not None:
                self.do_yield(parent, child.text)

        return self.do_return()


class ExtractElements(FindElements):
    def do_yield(self, parent, child_text):
        if child_text in self.my_names:
            self.my_target.append(deepcopy(parent))

    def do_return(self):
        return self.my_target


class FetchElements(FindElements):
    def do_yield(self, parent, child_text):
        self.my_names.add(child_text)

    def do_return(self):
        return self.my_names


class PruneFalseElements(FindElements):
    def do_yield(self, parent, child_text):
        if child_text in ('false', 'None'):
            parent.getparent().remove(parent)

    def do_return(self):
        return self.my_source


def prune_elements(root, test_mode=False):
    """Removes classAccesses elements that are not enabled.

    >>> root = prune_elements(example_profile_metadata_source(), True)
    >>> print_tree(root)
    <?xml version='1.0' encoding='UTF-8'?>
    <Profile xmlns="http://soap.sforce.com/2006/04/metadata">
      <classAccesses>
        <apexClass>AccountAddressManager</apexClass>
        <enabled>true</enabled>
      </classAccesses>
    </Profile>
    <BLANKLINE>
    """
    my_prune_elements = PruneFalseElements()
    my_prune_elements.my_test_mode = test_mode

    for parent_name in PARENTS:
        children = PARENTS.get(parent_name)
        # do(source, target, parent_name, child_name, names):
        root = my_prune_elements.do(root, None, parent_name,
                                    children[PRUNE_CHILD], None)
    return root


def fetch_elements(root, parent_name, test_mode=False):
    """Harvests element names.

    >>> root = prune_elements(example_profile_metadata_target(), True)
    >>> names = fetch_elements(root,'classAccesses', True)
    >>> print names 
    set(['AccountHierarchyBuilder', 'AccountAddressManager'])
    """
    my_fetch_elements = FetchElements()
    my_fetch_elements.my_test_mode = test_mode

    names = set()
    children = PARENTS.get(parent_name)
    names = my_fetch_elements.do(root, None, parent_name,
                                 children[FETCH_CHILD], names)

    return set() if names is None else names


def diff_elements(source, target, parent_name, test_mode=False):
    """Identifies the names of elements in target but not in source. 
    Target must be a superset of source.

    >>> source = prune_elements(example_profile_metadata_source(), True)
    >>> target = prune_elements(example_profile_metadata_target(), True)
    >>> names = diff_elements(source,target,'classAccesses', True)
    >>> print names
    set(['AccountHierarchyBuilder'])

    """
    source_names = fetch_elements(source, parent_name, test_mode)
    target_names = fetch_elements(target, parent_name, test_mode)
    names = target_names.difference(source_names)
    return names


def prune_tree(profile_path):
    """Raises IOError if profile_path cannot be parsed.
    """
    profile_tree = etree.parse(profile_path)
    profile_root = prune_elements(profile_tree.getroot())
    return profile_root


def main_check_values(profile_path_source, profile_path_target, profile_path_output):
    if profile_path_source is None or profile_path_target is None or profile_path_output is None:
        raise ValueError(
            "Three parameters are required: profile_path_source, "
            "profile_path_target, and profile_path_output")


def main_prune_source(profile_path_source):
    try:
        source_root = prune_tree(profile_path_source)
    except IOError:
        # Info error only. Not exception.
        print "{profile_path_source} is not available.".format(
            profile_path_source=profile_path_source)
        exit(1)
    return source_root


def main_prune_target(profile_path_target):
    try:
        target_root = prune_tree(profile_path_target)
    except IOError:
        # Info error only. Not exception.
        print "{profile_path_target} is not available.".format(
            profile_path_target=profile_path_target)
        exit(1)
    return target_root


def extract_elements(source_root, target_root, root_name='Profile', test_mode=False):
    """Creates profile document from target containing the named elements.
    names = diff_elements(prune_elements(example_profile_source(),False),
                          target,False),False)

    >>> source_root = prune_elements(example_profile_metadata_source(), True)
    >>> target_root = prune_elements(example_profile_metadata_target(), True)
    >>> root = extract_elements(source_root,target_root,'Profile', True)
    >>> print_tree(root)
    <?xml version='1.0' encoding='UTF-8'?>
    <Profile xmlns="http://soap.sforce.com/2006/04/metadata">
      <classAccesses>
        <apexClass>AccountHierarchyBuilder</apexClass>
        <enabled>true</enabled>
      </classAccesses>
    </Profile>
    <BLANKLINE>
    """
    my_extract_elements = ExtractElements()
    my_extract_elements.my_test_mode = test_mode
    root = sforce_root(root_name)
    for parent_name in PARENTS:
        children = PARENTS.get(parent_name)
        names = diff_elements(source_root, target_root, parent_name, test_mode)
        root = my_extract_elements.do(target_root, root, parent_name,
                                      children[EXTRACT_CHILD], names)
    return root


def is_profile(profile_path_output):
    return '.profile' in profile_path_output


def root_name(profile_path_output):
    return 'Profile' if is_profile(profile_path_output) else 'PermissionSet'


def main(profile_path_source, profile_path_target, profile_path_output):
    """Reads profiles from file system and renders delta profile to profile_path_output.
    """
    main_check_values(profile_path_source, profile_path_target, profile_path_output)
    source_root = main_prune_source(profile_path_source)
    target_root = main_prune_target(profile_path_target)
    output_name = root_name(profile_path_output)
    root = extract_elements(source_root, target_root, output_name)
    # (TBD) - Fake it until you can make it KZN-673
    if not is_profile(profile_path_output):
        my_element = etree.SubElement(root,'label')
        my_element.text = 'Community Hub Guest'
        root.append(my_element)
    save_tree(root, profile_path_output)
    return 0


if __name__ == '__main__':
    if len(argv) == 4:
        main(argv[1], argv[2], argv[3])
    else:
        profile_path_source = None
        profile_path_target = None
        profile_path_output = None
        try:
            profile_path_source = environ['profile_path_source']
            profile_path_target = environ['profile_path_target']
            profile_path_output = environ['profile_path_output']
        except KeyError:
            print "Requires profile_path_source, profile_path_target, and \
            profile_path_output as parameters or system properties, where  \
            source is the profile with the lower major version number. \
            The upgrade profile document is saved to profile_path_output."
            exit(1)
        main(profile_path_source, profile_path_target, profile_path_output)
