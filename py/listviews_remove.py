#!/usr/bin/python
import argparse
from os import environ, path
from sys import exit

from lxml import etree

from tools_lxml import print_tree, save_tree, sforce_root, field_sets_element, list_views_element, namespace_prepend, namespace_declare

"""Remove the ListView elements from the Account and Contact objects."""
"""
Use Case for listviews_remove.py

Motivation: The Account and Contact ListViews are checked into the 
repository to simplify development, but are not meant to be packaged. 
Accordingly, we remove the listviews when deploying to the packaging org. 

Stakeholders: Release Engineering

Output: Well-formed Account and Contact object with no ListView elements. 

Success Scenario:
1. External actor invokes script from command line passing the path to 
the source directory.
2. Script passes argument to main, which orchestrates the process.
3. Process reads object documents into an lxml etree, pruning the tree to
remove ListView elements.
4. Process outputs the updated object as a well-formed XML document. 
"""

def example_account_object():
    """Generates an example Account  document.
    >>> root = example_account_object()
    >>> print_tree(root)
    <?xml version='1.0' encoding='UTF-8'?>
    <CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
      <fieldSets>
        <fullName>CompanySearchResults</fullName>
        <description>Create Company Account</description>
        <displayedFields>
          <field>AccountNumber</field>
          <isFieldManaged>false</isFieldManaged>
          <isRequired>false</isRequired>
        </displayedFields>
      </fieldSets>
      <fieldSets>
        <fullName>CompanyMatchingAccounts</fullName>
        <description>Company Search Result card</description>
        <displayedFields>
          <field>AnnualRevenue</field>
          <isFieldManaged>false</isFieldManaged>
          <isRequired>false</isRequired>
        </displayedFields>
      </fieldSets>
      <listViews>
        <fullName>AllAccounts</fullName>
        <columns>ACCOUNT.NAME</columns>
        <filterScope>Everything</filterScope>
        <label>All Accounts</label>
      </listViews>
      <listViews>
        <fullName>NewThisWeek</fullName>
        <columns>ACCOUNT.NAME</columns>
        <filterScope>Everything</filterScope>
        <label>New This Week</label>
      </listViews>
    </CustomObject>
    <BLANKLINE>
    """
    root = sforce_root('CustomObject')
    root = field_sets_element(root,'CompanySearchResults',
                              'Create Company Account','AccountNumber',
                              'false', 'false')
    root = field_sets_element(root, 'CompanyMatchingAccounts',
                          'Company Search Result card', 'AnnualRevenue',
                          'false','false')
    root = list_views_element(root, 'AllAccounts', 'ACCOUNT.NAME',
                              'Everything', 'All Accounts')
    root = list_views_element(root, 'NewThisWeek', 'ACCOUNT.NAME',
                              'Everything', 'New This Week')
    return root


def strip_listviews(root, test_mode=False):
    """Removes listview elements from etree.

    >>> root = strip_listviews(example_account_object(), True)
    >>> print_tree(root)
    <?xml version='1.0' encoding='UTF-8'?>
    <CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
      <fieldSets>
        <fullName>CompanySearchResults</fullName>
        <description>Create Company Account</description>
        <displayedFields>
          <field>AccountNumber</field>
          <isFieldManaged>false</isFieldManaged>
          <isRequired>false</isRequired>
        </displayedFields>
      </fieldSets>
      <fieldSets>
        <fullName>CompanyMatchingAccounts</fullName>
        <description>Company Search Result card</description>
        <displayedFields>
          <field>AnnualRevenue</field>
          <isFieldManaged>false</isFieldManaged>
          <isRequired>false</isRequired>
        </displayedFields>
      </fieldSets>
    </CustomObject>
    <BLANKLINE>
    """
    # etree.strip_elements(root, 'listViews') -- Does not support namespace
    ns = namespace_declare(test_mode)
    list_views_match = namespace_prepend('listViews', test_mode)
    list_views = root.findall(list_views_match, ns)
    for list_view in list_views:
        list_view.getparent().remove(list_view)

    return root


def main_verify_object(homedir,component):
    filename = path.join(homedir, 'src/objects/' + component + '.object')
    if not path.isfile(filename):
        print "The " + component + "object does not exist: {}".format(filename)
        exit(1)
    return filename


def main_parse_file(filename):
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(filename, parser)


def do_component(component):
    filename = main_verify_object(homedir, component)
    tree = main_parse_file(filename)
    root = strip_listviews(tree.getroot())
    if root is not None:
        save_tree(root, filename)
    else:
        print "The " + component + "file is not a valid XML document."
        exit(0)


def main(homedir):
    """Reads Account and Contact object and writes modified document
    from and to the file system.
    """
    do_component('Account')
    do_component('Contact')
    return 0


def __parser_config():
    parser = argparse.ArgumentParser(description="Updates the Account and Contact "
                                                 "objects to remove listViews elements.",
                                     epilog="The parameter may also be passed "
                                            "as an environment variable.")
    parser.add_argument('-d', '--homedir', help="The folder holding the "
                                                "Salesforce metadata.")
    return parser


def __args_verify(homedir):
    if homedir is None:
        print "Requires homedir as a parameter or system property."
        exit(1)
    if not path.exists(homedir):
        print "The homedir does not exist: {}".format(homedir)
        exit(1)


if __name__ == '__main__':
    homedir = None
    try:
        homedir = environ['homedir']
    except KeyError:
        pass

    parser = __parser_config()
    args = parser.parse_args()

    homedir = args.homedir if args.homedir is not None else homedir
    __args_verify(homedir)

    main(homedir)
