#!/usr/bin/python
"""Centralize mdt prefixing utilities used by multiple packages.
"""

from glob import glob
from os import path
from re import match, search, sub, IGNORECASE
from tools_lxml import namespace_declare, load_tree, save_tree


class Namespacer:

    @staticmethod
    def regex_replacer(pattern, repl):
        """Returns a function that returns the result of a regex substitution on its input."""
        return lambda x: sub(pattern, repl, x)

    def __init__(self, prefix, sourcedir, page_urls):
        self.prefix = prefix
        self.sourcedir = sourcedir
        self.page_urls = page_urls
        self.underscore_namespacer = self.regex_replacer("^(?!" + self.prefix + "__)", self.prefix + "__")
        self.dot_namespacer = self.regex_replacer("^(?!" + self.prefix + r"\.)", self.prefix + ".")

    @staticmethod
    def get_field_element(tree, field):
        """Finds the xml element for the specified field."""
        return tree.xpath("//md:values[md:field/text()='" + field + "']/md:value",
                          namespaces=namespace_declare())[0]

    def process(self, obj_type, fields, operation):
        """Applies a namespacing operation to the specified fields of a specified metadata object type.
        Operations include dot_namespacer and underscore_namespacer."""
        for filename in glob(path.join(self.sourcedir, "customMetadata/" + obj_type + ".*.md")):
            root = load_tree(filename)

            for field in fields:
                element = self.get_field_element(root, field)
                if not element.text is None:
                    element.text = operation(element.text)

            save_tree(root, filename)

    def is_datasource_record(self, name):
        """Checks whether the name refers to a datasource record, as opposed to a class."""
        my_path = path.join(self.sourcedir, "customMetadata/DataSource2." + name + ".md")
        return path.isfile(my_path)

    def datasource_namespacer(self,value):
        """Applies either a underscore or dot namespace based on whether the value isreg
        the name of a datasource record or a class"""
        # already has namespace, skip
        if match("^" + self.prefix + r"(?:\.|__)", value):
            return value
        # is the name of a datasource record, apply underscore namespace
        if self.is_datasource_record(value):
            return self.underscore_namespacer(value)
        # is the name of a class, apply dot namespace
        return self.dot_namespacer(value)

    def url_needs_namespace(self,url):
        """Urls need to be namespaced if they contain no /'s other than optionally at the
        start, and the url is not found in page_urls."""
        if match(r"^\w+:\/\/", url):
            return False
        if search(self.prefix + "__", url, flags=IGNORECASE) is not None:
            return False
        if match(r"^/?[^/]+$", url):
            if not url.startswith("/"):
                url = "/" + url
            return not url in self.page_urls
        return False

    def url_namespacer(self,value):
        """Applies namespaces to urls, after an optional leading '/apex/' or '/'."""
        if self.url_needs_namespace(value):
            return sub(r"^(/apex/|/|)(.*)", r"\1" + self.prefix.lower() + r"__\2", value)
        return value
