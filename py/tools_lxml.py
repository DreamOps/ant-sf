#!/usr/bin/python
"""Centralize lxml utilities used by multiple nu modules.
"""
from lxml import etree

# Defines the Salesforce metadata namespace and metadata prefix
SF_URI = 'http://soap.sforce.com/2006/04/metadata'
SF_PREFIX = 'md'


def namespace_declare(test_mode=False):
    """Returns None for test mode, or the SF namespace reference

    >>> print namespace_declare()
    {'md': 'http://soap.sforce.com/2006/04/metadata'}
    >>> print namespace_declare(True)
    None

    """
    return None if test_mode else {SF_PREFIX: SF_URI}


def namespace_prepend(match_string, test_mode=False):
    """Omits the namespace prefix during test mode.

    >>> print namespace_prepend('match_string')
    md:match_string
    >>> print namespace_prepend('match_string', True)
    match_string
    """
    return match_string if test_mode else SF_PREFIX + ':' + match_string

def load_tree(filename):
    """Loads an XML document as an etree."""
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(filename, parser)

def save_tree(root, filename):
    """Saves etree as XML document and raises IOError for any problem."""
    f = open(filename, 'w')
    f.write(etree.tostring(root, pretty_print=True, encoding='UTF-8',
                         xml_declaration=True))
    f.close()

def print_tree(root):
    """Renders an XML document with indentation and an XML declaration
    using UTF-8 encoding (per Salesforce).

    >>> root = sforce_root('root')
    >>> print_tree(root)
    <?xml version='1.0' encoding='UTF-8'?>
    <root xmlns="http://soap.sforce.com/2006/04/metadata"/>
    <BLANKLINE>

    """
    print(etree.tostring(root, pretty_print=True, encoding='UTF-8',
                         xml_declaration=True))


def sforce_root(root_name):
    """Generates the root element of a sforce metadata document.
    This function is used to create example metadata documents.

    >>> from lxml import etree
    >>> root = sforce_root('ExampleNode')
    >>> print_tree(root)
    <?xml version='1.0' encoding='UTF-8'?>
    <ExampleNode xmlns="http://soap.sforce.com/2006/04/metadata"/>
    <BLANKLINE>
    """
    sf_tag = '{%s}' % SF_URI
    nsmap = {None: SF_URI}
    root = etree.Element(sf_tag + root_name, nsmap=nsmap)
    return root


def sub_element_text(my_parent,my_tag,my_text):
    my_element = etree.SubElement(my_parent,my_tag)
    my_element.text = my_text
    return my_element


def field_sets_element(root, full_name, description, field, is_field_managed,
                       is_required):
    field_sets = etree.SubElement(root, 'fieldSets')
    sub_element_text(field_sets, 'fullName', full_name)
    sub_element_text(field_sets, 'description', description)
    displayed_fields = etree.SubElement(field_sets, 'displayedFields')
    sub_element_text(displayed_fields, 'field', field)
    sub_element_text(displayed_fields, 'isFieldManaged', is_field_managed)
    sub_element_text(displayed_fields, 'isRequired', is_required)
    return root


def fields_element(root, full_name, default_value, description,
                   external_id, inline_help_text, label,
                   track_feed_history, track_history, type):
    fields = etree.SubElement(root, 'fields')
    sub_element_text(fields, 'fullName', full_name)
    sub_element_text(fields, 'default_value', default_value)
    sub_element_text(fields, 'description', description)
    sub_element_text(fields, 'external_id', external_id)
    sub_element_text(fields, 'inline_help_text', inline_help_text)
    sub_element_text(fields, 'label', label)
    sub_element_text(fields, 'track_feed_history', track_feed_history)
    sub_element_text(fields, 'track_history', track_history)
    sub_element_text(fields, 'type', type )
    return root


def list_views_element(root, full_name, columns, filter_scope, label):
    list_views = etree.SubElement(root, 'listViews')
    sub_element_text(list_views, 'fullName', full_name)
    sub_element_text(list_views, 'columns', columns)
    sub_element_text(list_views, 'filterScope', filter_scope)
    sub_element_text(list_views, 'label', label)
    return root


def weblinks_element(root, full_name, availability, display_type, height,
                     link_type, master_label, open_type, page, protected):
    web_links = etree.SubElement(root, 'webLinks')
    sub_element_text(web_links, 'fullName', full_name)
    sub_element_text(web_links, 'availability', availability)
    sub_element_text(web_links, 'displayType', display_type)
    sub_element_text(web_links, 'height', height)
    sub_element_text(web_links, 'linkType', link_type)
    sub_element_text(web_links, 'masterLabel', master_label)
    sub_element_text(web_links, 'openType', open_type)
    sub_element_text(web_links, 'page', page)
    sub_element_text(web_links, 'protected', protected)
    return root
