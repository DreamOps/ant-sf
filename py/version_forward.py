#!/usr/bin/python
"""For one or more package prefixes, updates metadata references to match 
the installed version. Note that this script directly changes the local 
copy of matching classes. Requires homedir, sf_xmlns as parameters or 
system properties.

To call from the Python CLI (with metadata present): 
    ./version_match.py -d=~/git/example-org

To call from the Ant CLI: ant -Dhome={} -Dsf_credentials={} 
    -Dsf_pkgns=PREFIX1,PREFIX2,PREFIX3 version

To run the embedded tests: python -m doctest -v version_match.py

Usage:
    main('/Users/thusted/git/example-org')
    Set 66 classes to PREFIX1 6.3.
    Set 0 classes to PREFIX2 4.4.
    PREFIX3 is not installed.
"""
"""
Use Case for version_match.py

Motivation: Updates metadata references in Apex classes to match the installed 
version in order to avoid gaps when moving code between orgs. (The API will not 
deploy code set to a prior version if that version was never installed to the 
receiving org, so this script brings all the references current.)

Stakeholders: Release Engineering

Output: Updated Apex class metadata files for any class set to a prior version. 

Prerequesite: The installed package version metadata for the target org is 
retrieved, and the metadata to be deployed is also available locally.

Postrequesite: The updated metadata is deployed to the target org.

Assumptions: 
1. The version in the target org is equal-to or greater-than the versions given 
in the metadata. 

Success Scenario:
1. External actor invokes script from command line passing homedir and 
prefix_list arguments. 
2. Script evaluates arguments and passes source and target arguments to main, 
which orchestrates the process.
3. Process loops through the prefixes passed into the script and updates the 
version for each prefix. 
4. Process obtain the current major and minor version for the package prefix.
5. Using find_files, update_package_version loops through the Apex class
metadata, and calls modify_version.
6. modify_version parses each file, updating any versions that do not match.
7. update_package_version writes the updated metadata file if modified.
8. When all files are processed, update_package_version prints the number of
metadata files modified.
9. Process repeats from step 4 for each prefix and exits.

Alternate Scenario:

(1a)
1. External actor sets environment properties "profile_path_source" and
"profile_path_target", and passes no arguments.

(2a)
1. Script detects missing arguments and prints help message.
** "Requires homedir, sf_prefix_list as parameters or system properties."

(7a)
1. Package versions match and unmodified file is not written back.
"""
import argparse
from os import environ, path
from sys import exit

from lxml import etree

from tools_io import find_files
from tools_lxml import print_tree, sforce_root, namespace_declare, namespace_prepend


def example_installed_package():
    """Generates an example InstalledPackage metadata document.

    >>> root = example_installed_package()
    >>> print_tree(root)
    <?xml version='1.0' encoding='UTF-8'?>
    <InstalledPackage xmlns="http://soap.sforce.com/2006/04/metadata">
      <versionNumber>1.2.3</versionNumber>
    </InstalledPackage>
    <BLANKLINE>
    """
    root = sforce_root('InstalledPackage')
    version_number = etree.SubElement(root, 'versionNumber')
    version_number.text = '1.2.3'
    return root


def get_version(root):
    """Retrieves the major and minor versions from a InstalledPackage
    document.

    >>> root = example_installed_package()
    >>> (majorNumber,minorNumber) = get_version(root)
    >>> ok = (majorNumber,minorNumber) == ('1','2')
    >>> ok
    True
    """
    vn = root.xpath('string()').strip()
    split = vn.split('.')
    major_number = split[0]
    minor_number = split[1]
    # noinspection PyRedundantParentheses
    return (major_number, minor_number)


def example_apex_class():
    """Generates the XML tree representing an example ApexClass metadata
    document.

    >>> root = example_apex_class()
    >>> print_tree(root)
    <?xml version='1.0' encoding='UTF-8'?>
    <ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
      <apiVerson>12.0</apiVerson>
      <packageVersions>
        <majorNumber>1</majorNumber>
        <minorNumber>2</minorNumber>
        <namespace>Example</namespace>
      </packageVersions>
      <status>Active</status>
    </ApexClass>
    <BLANKLINE>
    """
    root = sforce_root('ApexClass')
    api_version = etree.SubElement(root, 'apiVerson')
    package_versions = etree.SubElement(root, 'packageVersions')
    status = etree.SubElement(root, 'status')
    api_version.text = '12.0'
    status.text = 'Active'
    major_number = etree.SubElement(package_versions, 'majorNumber')
    minor_number = etree.SubElement(package_versions, 'minorNumber')
    namespace = etree.SubElement(package_versions, 'namespace')
    major_number.text = '1'
    minor_number.text = '2'
    namespace.text = 'Example'
    return root


def conform_node(modified, element, node_text, parent, ns, test_mode):
    my_element = namespace_prepend(element, test_mode)
    node = parent.find(my_element, ns)
    if node.text != node_text:
        node.text = node_text
        modified = True

    return modified


def modify_version(root, prefix, major_number, minor_number, test_mode=False):
    """Scans the major and minor version numbers in the packageVersions
    nodes, and updates as needed for the given prefix.

    >>> init_root = example_apex_class()
    >>> root = modify_version(init_root,'Example','3','4',True)
    >>> ok = (root is not None)
    >>> ok
    True
    >>> print_tree(root)
    <?xml version='1.0' encoding='UTF-8'?>
    <ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
      <apiVerson>12.0</apiVerson>
      <packageVersions>
        <majorNumber>3</majorNumber>
        <minorNumber>4</minorNumber>
        <namespace>Example</namespace>
      </packageVersions>
      <status>Active</status>
    </ApexClass>
    <BLANKLINE>
    """
    modified = False
    ns = namespace_declare(test_mode)
    packageVersions = namespace_prepend('packageVersions', test_mode)
    pv = root.findall(packageVersions, ns)
    for parent in pv:
        for child in parent:
            if child.text == prefix:
                modified = conform_node(modified, 'majorNumber', major_number, parent, ns, test_mode)
                modified = conform_node(modified, 'minorNumber', minor_number, parent, ns, test_mode)

    return root if modified else None


def write_metadata(filename, root):
    with open(filename, 'w') as text_file:
        text_file.write(etree.tostring(root, pretty_print=True,
                                       encoding='UTF-8', xml_declaration=True))
        text_file.close()


def conform_metadata(prefix, sourcedir, sourcepattern, major_number, minor_number):
    """Updates Apex class metadata files to the installed version for the package corresponding to the prefix. """
    count = 0
    for filename in find_files(sourcedir, sourcepattern):
        tree = etree.parse(filename)
        root = modify_version(tree.getroot(), prefix, major_number, minor_number)
        if root is not None:
            write_metadata(filename, root)
            count += 1

    return count


def update_package_version(prefix, prefixdir, sourcedirs,
                           sourcepattern):
    """Loops through classes and sets version reference for a given prefix.
    Requires - opt/installedPackages retrieved from org. Returns a message
    if package not installed (does not raise exception).
    """
    try:
        tree = etree.parse(prefixdir)
    except IOError:
        # Info error only. Continue for any other prefixes.
        return "{prefix} is not installed to {prefixdir}.".format(prefix=prefix,prefixdir=prefixdir)

    (major_number, minor_number) = get_version(tree.getroot())

    for sourcedir in sourcedirs:
        count = conform_metadata(prefix, sourcedir, sourcepattern, major_number, minor_number)

    # returns number of modified files
    return "Set {count} metadata files to {prefix} {majorNumber}.{minorNumber}."\
        .format(count=count, prefix=prefix, majorNumber=major_number,
        minorNumber=minor_number)


def main(homedir, prefix_list):
    """Parses one or more prefixes and loops through each prefix to update
  relevant classes.
  """
    prefixes = [x.strip() for x in prefix_list.split(',')]
    for px in prefixes:
        prefixdir = path.join(homedir, 'opt/installedPackages', px+'.installedPackage')
        sourcedirs = [path.join(homedir, 'src/classes'),path.join(homedir, 'src/components'),
                      path.join(homedir, 'src/pages'), path.join(homedir, 'src/triggers'),
                      path.join(homedir, 'src/email')]
        log = update_package_version(px, prefixdir, sourcedirs, '*.*-meta.xml')
        print(log)


def __parser_config():
    parser = argparse.ArgumentParser(description="For one or more package "
                                                 "prefixes, updates metadata "
                                                 "references to match the "
                                                 "installed version.",
                                     epilog="The parameters may also be passed "
                                            "as environment variables.")
    parser.add_argument('-d', '--homedir', help="The folder holding the "
                                                "Salesforce metadata.")
    parser.add_argument('-s', '--sf_prefix_list', help="The list of managed "
                                                      "packages to process.")
    return parser


def __args_verify(homedir,sf_prefix_list):
    if homedir is None or sf_prefix_list is None:
        print "Requires homedir, sf_prefix_list as parameters or system " \
              "properties."
        exit(1)
    if not path.exists(homedir):
        print "The homedir does not exist: {}".format(homedir)
        exit(1)


if __name__ == '__main__':
    homedir = None
    sf_prefix_list = None
    try:
        homedir = environ['homedir']
        sf_prefix_list = environ['sf_prefix_list']
    except KeyError:
        pass

    args = __parser_config().parse_args()

    # CLI arguments have precedence
    homedir = args.homedir if args.homedir is not None else homedir
    sf_prefix_list = args.sf_prefix_list if args.sf_prefix_list is not None else sf_prefix_list

    __args_verify(homedir,sf_prefix_list)

    main(homedir, sf_prefix_list)
