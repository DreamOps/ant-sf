#!/usr/bin/python
"""Builds ZLabels class to ensure all Custom Labels are packaged.

To call from the Python CLI (with metadata present):
    % ./zlabels_build.py -d ~/git/sf-org -v 38.0

To call from the Ant CLI: ant -Dhomedir=sf-org
                              -Dsf_apiVersion=38.0
"""
"""
Use Case for zlabels_build

Motivation: Labels are only packaged when there is a direct reference, and some
of our labels are used indirectly. The ZLabels class is created so that there
is a direct reference to each label, ensuring all labels are packaged.

Stakeholders: Release Engineering

Output: ZLabels.cls and ZLabels.cls-meta.xml

Prerequisite: The development metadata is checked-out, including the labels
folder.

Postrequisite: The metadata is depoloyed to the packaging org.

Assumptions:
1. All labels should be packaged.

Success Scenario:
1. External actor invokes script from command line, passing homedir as an
argument.
2. Script evaluates arguments and invokes main, which controls the process.
3. Process parses CustomLabels.labels document into an etree.
4. Process finds the fullName for each label and appends to a list.
5. Process writes class header to ZLabels.cls file, writes labels. and
writes class footer.
6. Process writes metadata file.

"""
import argparse
from os import environ, path
from sys import exit

from lxml import etree

from tools_lxml import namespace_declare, namespace_prepend, print_tree, \
    sforce_root, sub_element_text

# ---- NOTE TO READER ----
# In Python, all functions must be declared before they are used.
# The best way to read the source is to start at the end with the
# main function, and step up.
# ----

default_api_version = '38.0'

def labels_element(root, full_name_text, categories_text, language_text,
                       protected_text, shortDescription_text, value_text):
    labels = etree.SubElement(root, 'labels')
    sub_element_text(labels, 'fullName', full_name_text)
    sub_element_text(labels, 'categories', categories_text)
    sub_element_text(labels,'language',language_text)
    sub_element_text(labels,'protected',protected_text)
    sub_element_text(labels,'description',shortDescription_text)
    sub_element_text(labels,'value', value_text)
    return root


def example_Label_object():
    """Generates an example Label metadata document.
    >>> root = example_Label_object()
    >>> print_tree(root)
    <?xml version='1.0' encoding='UTF-8'?>
    <CustomLabels xmlns="http://soap.sforce.com/2006/04/metadata">
      <labels>
        <fullName>AColleague</fullName>
        <categories>ChooseAnAttendee</categories>
        <language>en_US</language>
        <protected>true</protected>
        <description>A Colleague</description>
        <value>A Colleague</value>
      </labels>
      <labels>
        <fullName>ZipPostalCode</fullName>
        <categories>Address</categories>
        <language>en_US</language>
        <protected>true</protected>
        <description>A ZipPostalCode</description>
        <value>Zip/Postal Code</value>
      </labels>
    </CustomLabels>
    <BLANKLINE>
    """
    root = sforce_root('CustomLabels')
    root = labels_element(root,'AColleague','ChooseAnAttendee','en_US','true','A Colleague','A Colleague')
    root = labels_element(root,'ZipPostalCode','Address','en_US','true','A ZipPostalCode','Zip/Postal Code')
    return root


def extract_labels(root, test_mode=False):
    ns = namespace_declare(test_mode)
    match_labels = namespace_prepend('labels', test_mode)
    return root.findall(match_labels,ns)


def extract_full_name(root, test_mode=False):
    """Returns list of label full names.

    >>> names = []
    >>> names = extract_full_name(example_Label_object(),True)
    >>> print names
    ['Label.AColleague', 'Label.ZipPostalCode']
    """

    labels = extract_labels(root, test_mode)
    match_fullName = namespace_prepend('fullName', test_mode)
    ns = namespace_declare(test_mode)
    names = []

    for label in labels:
        names.append(
            'Label.' + label.findtext(match_fullName, default='', namespaces=ns))
    return names


def build_class(names):
    """ Format ZLabels class file.

    >>> names = ['Label.AColleague', 'Label.ZipPostalCode']
    >>> output = build_class(names)
    >>> print output
    @isTest
    private class ZLabels {
        private static List<String> labels = new List<String> {
            Label.AColleague,
            Label.ZipPostalCode
        };
    }
    <BLANKLINE>
    """
    header = '@isTest\nprivate class ZLabels {\n    private static List<String> labels = new List<String> {\n'
    footer = '    };\n}\n'
    content = ''.join('        ' + n + ',' + '\n' for n in names)
    content = content[:-2] + '\n'
    return header + content + footer


def build_meta():
    """Format ZLabels metadata file.

    >>> output = build_meta()
    >>> print output
    <?xml version="1.0" encoding="UTF-8"?>
    <ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
        <apiVersion>35.0</apiVersion>
        <status>Active</status>
    </ApexClass>
    <BLANKLINE>
    """
    output = '<?xml version="1.0" encoding="UTF-8"?>\n<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">\n    <apiVersion>' + default_api_version + '</apiVersion>\n    <status>Active</status>\n</ApexClass>\n'
    return output


def main_write_zlabels_metadata(homedir):
    f = open(path.join(homedir, 'src/classes', 'ZLabels.cls-meta.xml'), 'w')
    f.write(build_meta())
    f.close()


def main_write_zlabels_class(homedir, zlabel_class):
    f = open(path.join(homedir, 'src/classes', 'ZLabels.cls'), 'w')
    f.write(zlabel_class)
    f.close()


def main_zlabels_class(root):
    names = extract_full_name(root)
    return build_class(names)


def main_labels_metadata(homedir):
    filename = path.join(homedir, 'src/labels', 'CustomLabels.labels')
    tree = etree.parse(filename)
    return tree.getroot()


def main(homedir, sf_apiVersion):
    global default_api_version
    if sf_apiVersion is not None:
        default_api_version = sf_apiVersion
    labels_metadata = main_labels_metadata(homedir)
    zlabel_class = main_zlabels_class(labels_metadata)
    main_write_zlabels_class(homedir, zlabel_class)
    main_write_zlabels_metadata(homedir)
    return 0


def __parser_config():
    parser = argparse.ArgumentParser(description="Builds ZLabels class to "
                                                 "ensure all Custom Labels are "
                                                 "packaged.",
                                     epilog="The parameters may also be passed "
                                            "as environment variables.")
    parser.add_argument('-d', '--homedir', help="The folder holding the "
                                                "Salesforce metadata.")
    parser.add_argument('-v', '--sf_apiVersion', help="The API version to include "
                                                   "in the metadata file.")
    return parser


def __args_verify(homedir):
    if homedir is None:
        print "Requires homedir as a parameter or system property."
        exit(1)
    else:
        if not path.exists(homedir):
            print "The homedir does not exist: {}".format(homedir)
            exit(1)


if __name__ == '__main__':
    homedir = None
    sf_apiVersion = None
    try:
        homedir = environ['homedir']
        sf_apiVersion = environ['sf_apiVersion']
    except KeyError:
        pass

    parser = __parser_config()
    args = parser.parse_args()

    homedir = args.homedir if args.homedir is not None else homedir
    __args_verify(homedir)

    sf_apiVersion = args.sf_apiVersion if args.sf_apiVersion is not None else sf_apiVersion

    main(homedir, sf_apiVersion)
