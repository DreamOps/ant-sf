#!/usr/bin/python
"""Updates the Account object fieldSet elements to include expected Account
fields in either the displayedFields list or the availableFields list.

To call from the Python CLI (with metadata present):
    ./fieldsets_extend.py -d=~/git/example-org

To run the embedded tests: python -m doctest -v fieldsets_extend.py

Usage:
    main('/Users/thusted/git/example-org')
"""
"""
Use Case for fieldsets script

Motivation: To use a fieldSet, the Cards UI needs all the fields in an
Account fieldset to be either a "displayed field" or an "available field".
The default Account object lists only the displayed fields, and so we need
to inject the list of available fields, so that all expected fields are
found one list or the other.

Stakeholders: Developers using our Cards UI.

Output: Script modifies the Account.object document by adding a set of
"availableFields" to each fieldSets elements as needed.

Prerequisite:
* The master list of fields to make available.
* The Account document is checked out to the src/objects folder.

Postrequisite: Account object is deployed to an org with package installed.

Assumptions:
1. The master list of fields to make available is relatively static and
can be hardcoded into a script.
2. The object has a displayedFields elements with no availableFields elements.

Success Scenario:
1. External actor invokes script from command line passing homedir argument.
2. Script passes arguments to main, which controls the process.
3. For each fieldSets element, process loads the list of displayed fields
elements, and creates a list of displayedFields names for that fieldSet.
4. Process reads each master field, and if the field is not in the displayed
fields list, appends the field to an add available list.
5. For each field name in the add available list, process appends an
availableFields element to the current field set.
6. Main updates the object document with any changes.
"""
import argparse
from os import environ, path
from sys import exit

from lxml import etree

from tools_lxml import print_tree, save_tree, sforce_root, sub_element_text, field_sets_element, namespace_declare, namespace_prepend


FIELD_LIST = ["AccountNumber", "AccountSource", "AnnualRevenue", "BillingCity",
              "BillingCountry", "BillingLatitude", "BillingLongitude",
              "BillingPostalCode", "BillingState", "BillingStreet",
              "Description", "Fax", "Industry", "IsPersonAccount",
              "LastActivityDate", "LastReferencedDate", "LastViewedDate",
              "MasterRecordId", "Name", "NumberOfEmployees", "OwnerId",
              "Ownership", "ParentId", "Phone", "PhotoUrl", "Rating",
              "RecordTypeId", "Salutation", "ShippingCity", "ShippingCountry",
              "ShippingLatitude", "ShippingLongitude", "ShippingPostalCode",
              "ShippingState", "ShippingStreet", "TickerSymbol", "Type",
              "Website", "FirstName", "LastName", "PersonAssistantName",
              "PersonAssistantPhone", "PersonBirthDate", "PersonContactId",
              "PersonDepartment", "PersonEmail", "PersonEmailBouncedDate",
              "PersonHasOptedOutOfEmail", "PersonHomePhone",
              "PersonLastCURequestDate", "PersonLastCUUpdateDate",
              "PersonLeadSource", "PersonMailingCity", "PersonMailingLatitude",
              "PersonMailingLongitude", "PersonMailingStreet",
              "PersonMobilePhone", "PersonOtherCity", "PersonOtherCountry",
              "PersonOtherPostalCode", "PersonOtherState",
              "PersonOtherLatitude", "PersonOtherLongitude",
              "PersonOtherPhone", "PersonOtherStreet", "PersonTitle"]

TEST_LIST = ["AccountNumber", "AccountSource", "AnnualRevenue"]


def example_Account_object():
    """Generates an example InstalledPackage metadata document.
    >>> root = example_Account_object()
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
    root = sforce_root('CustomObject')
    root = field_sets_element(root,'CompanySearchResults',
                              'Create Company Account','AccountNumber',
                              'false', 'false')
    root = field_sets_element(root, 'CompanyMatchingAccounts',
                          'Company Search Result card', 'AnnualRevenue',
                          'false','false')
    return root


def modify_field_sets(root, fields, test_mode=False):
    """
    >>> root = modify_field_sets(example_Account_object(), TEST_LIST, True)
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
        <availableFields>
          <field>AccountSource</field>
          <isFieldManaged>false</isFieldManaged>
          <isRequired>false</isRequired>
        </availableFields>
        <availableFields>
          <field>AnnualRevenue</field>
          <isFieldManaged>false</isFieldManaged>
          <isRequired>false</isRequired>
        </availableFields>
      </fieldSets>
      <fieldSets>
        <fullName>CompanyMatchingAccounts</fullName>
        <description>Company Search Result card</description>
        <displayedFields>
          <field>AnnualRevenue</field>
          <isFieldManaged>false</isFieldManaged>
          <isRequired>false</isRequired>
        </displayedFields>
        <availableFields>
          <field>AccountNumber</field>
          <isFieldManaged>false</isFieldManaged>
          <isRequired>false</isRequired>
        </availableFields>
        <availableFields>
          <field>AccountSource</field>
          <isFieldManaged>false</isFieldManaged>
          <isRequired>false</isRequired>
        </availableFields>
      </fieldSets>
    </CustomObject>
    <BLANKLINE>
    """
    modified = False
    ns = namespace_declare(test_mode)
    field_sets_match = namespace_prepend('fieldSets', test_mode)
    field_sets = root.findall(field_sets_match, ns)
    for field_set in field_sets:
        add_available = []
        displayedFields_match = namespace_prepend('displayedFields', test_mode)

        displayed_fields = field_set.findall(displayedFields_match, namespaces=ns)
        field_match = namespace_prepend('field', test_mode)
        displayed_list = []
        for field in displayed_fields:
            found = field.findtext(field_match, namespaces=ns)
            displayed_list.append(found)

        for field in fields:
            if field not in displayed_list:
                add_available.append(field)

        if len(add_available) > 0:
            for add_field in add_available:
                parent = etree.SubElement(field_set,'availableFields')
                field = etree.SubElement(parent,'field')
                field.text = add_field
                sub_element_text(parent, 'isFieldManaged','false')
                sub_element_text(parent, 'isRequired', 'false')
                modified = True

    return root if modified else sforce_root('CustomObject')


def main_verify_path(homedir):
    filename = path.join(homedir, 'src/objects/Account.object')
    if not path.isfile(filename):
        print "The Account object does not exist: {}".format(filename)
        exit(1)
    return filename


def main_parse_file(filename):
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(filename, parser)


def main(homedir):
    filename = main_verify_path(homedir)
    root = modify_field_sets(main_parse_file(filename), FIELD_LIST)
    if root is not None:
        save_tree(root, filename)
    else:
        print "The Account file is not a valid XML document."
        exit(0)


def __parser_config():
    parser = argparse.ArgumentParser(description="Updates the Account object "
                                                 "fieldSet elements to include "
                                                 "expected Account fields in "
                                                 "either the displayedFields "
                                                 "list or the availableFields "
                                                 "list.",
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
