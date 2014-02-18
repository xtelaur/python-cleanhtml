# coding: utf-8

"""
Library to clear HTML page and make it more readable.

"""

from __future__ import unicode_literals

import os
import sys
import re
import logging
import argparse
import codecs
import json

from bs4 import BeautifulSoup
from tld import get_tld
import requests


# TODO: move settings to external conf file
WRAP_WIDTH = 80
GLOBAL_EXCLUDE_CLASS = ["share", "comment", "disqus", "facebook", "googleplus",
                        "livejournal", "vkontakte", "module", "sidebar",
                        "moimoir", "odnoklassniki", "widget", "social",
                        "footer", "recommend", "player", "banner", "assessment",
                        "tag", "bottom", "billboard", "header"]
GLOBAL_EXCLUDE_ELEM = ["script", "noscript", "style"]
GLOBAL_INCLUDE_ELEM = ["h1", "h2", "h3", "h4", "h5", "h6", "p"]
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', "schema", "sites.json")


class CleanHtml(object):
    """
    """

    def __init__(self, url=None):
        """
        """
        if url:
            self.url = url.strip()

        self.content = None
        self.clean = []

        self.out_ext = "txt"
        self.out_dir = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), '..', "data", "out")

    def _get_path_part(self):
        """
        (text) -> tuple(path, file_name)

        Convert URL to file path and file name
        """
        url = self.url.strip().partition("//")[2]
        if url[-1] == "/":
            url = url[:-1]
        url = url.split("/")

        file_name = "{0}.{1}".format(os.path.splitext(url[-1])[0], self.out_ext)
        part_path = url[0:-1]
        file_path = os.path.join(self.out_dir, *part_path)
        return file_path, file_name

    def _get_file_path(self):
        """
        Return full path with filename to text output
        """
        return os.path.join(*self._get_path_part())

    def _get_sitename(self):
        """
        Extract site domain from page URL
        """
        return get_tld(self.url, fail_silently=True)

    @staticmethod
    def wrap_text(text, width=WRAP_WIDTH):
        r"""
        (text, int) -> text

        Words wrapping at specified width

        >>> CleanHtml().wrap_text("Hello World!", 5)
        u'Hello\nWorld!'
        >>> CleanHtml().wrap_text("Hello World!", 80)
        u'Hello World!'
        """
        def wrappper():
            it = iter(text.split(' '))
            word = next(it)
            yield word
            pos = len(word) - word.rfind('\n') - 1
            for word in it:
                if "\n" in word:
                    lines = word.split('\n')
                else:
                    lines = (word,)
                pos += len(lines[0]) + 1
                if pos > width:
                    yield '\n'
                    pos = len(lines[-1])
                else:
                    yield ' '
                    if len(lines) > 1:
                        pos = len(lines[-1])
                yield word

        return ''.join(wrappper())

    def save(self, dest=None):
        """
        Save result text to file
        """
        dest_dir_path = self._get_path_part()[0]
        if not os.path.exists(dest_dir_path):
            os.makedirs(dest_dir_path)

        dest_file = dest or os.path.join(self._get_file_path())
        with codecs.open(dest_file, 'w', "utf-8") as out:
            out.write(self.get_title() + "\n\n")
            out.writelines(self.clean)
            out.write("URL: {}".format(self.url))

    @staticmethod
    def convert_links(elem):
        """
        Replace <a href="URL">LINK</a> to [LINK] [URL]
        """
        for a in elem.findAll('a'):
            if 'href' in a.attrs:
                s = "[{0}] [{1}]".format(unicode(a.string).strip(), a['href'].strip())
                a.replaceWith(s)

    def get_encoding(self):
        """
        Return HTML page codepage
        """
        return self.content.original_encoding

    def get_body(self):
        """
        Return content of HTML <body></body>
        """
        return self.content.body

    def get_title(self):
        """
        Return title of current site page
        """
        return self.wrap_text(self.content.title.string.strip())

    def sitename(self):
        return self._get_sitename()

    def get_site_schema(self):
        """
        Retrun filtr configuration schema for current site
        """
        try:
            schema_file = open(SCHEMA_PATH, "r").read()
            schema = json.loads(schema_file).get(self.sitename(), {})
            return schema
        except IOError:
            print("Schema file read error!")

    def clear(self):
        """
        Clear html to more readability
        """
        pass

    def find_all_class(self, cls):
        """
        Find all 'cls' fragments on content.
        Return list.
        """
        find = self.content.findAll(attrs={'class': cls})
        return find

    def process(self, dest=None):
        """
        Processing HTML page - get from URL, clean and save to file
        """
        if not self.url:
            raise URLNotSpecified()

        html_page = requests.get(self.url)

        if html_page.status_code == requests.codes.ok:
            self.content = BeautifulSoup(html_page.content, "html5lib")
            self.convert_links(self.content.body)

            schema = self.get_site_schema()
            ex_class = schema.get("ex_class", GLOBAL_EXCLUDE_CLASS)
            in_class = schema.get("in_class", None)
            in_elem = schema.get("in_elem", None)

            # If we have in_elem in site schema then exclude only it
            if in_elem:
                for line in self.content.body.findAll(name=in_elem):
                    if line:
                        self.clean += "{0}\n\n".format(self.wrap_text(line.get_text(separator="\n", strip=True)))
            elif in_class:
                for line in self.content.body.findAll(attrs={'class': in_class}):
                    if line:
                        self.clean += "{0}\n\n".format(self.wrap_text(line.get_text(separator="\n\n", strip=True)))
            else:
                # Remove "script", "noscript", "style" etc.
                for block in GLOBAL_EXCLUDE_ELEM:
                    for line in self.content.body.findAll(name=block):
                        line.extract()

                # Remove tags with exclude class
                for cls in ex_class:
                    for line in self.content.body.findAll(attrs={'class': cls}):
                        line.extract()

                    for line in self.content.body.findAll(id=cls):
                        line.extract()

                for line in self.content.body.findAll(GLOBAL_INCLUDE_ELEM):
                    if line and line.get_text():
                        self.clean += "{0}\n\n".format(self.wrap_text(line.get_text(separator="\n\n", strip=True)))

            self.save(dest)
        else:
            raise PageLoadError()


class PageLoadError(Exception):
    """
    """
    pass


class InvalidURL(Exception):
    """
    """
    pass


class URLNotSpecified(Exception):
    """
    """
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Clean HTML page and save only text to file')
    parser.add_argument('url', nargs='?', type=str, help='Page URL')
    parser.add_argument('--savefile', nargs='?', type=str, help='File name to save result')
    parser.add_argument('--urlfile', nargs='?', type=str, help='Links list file')
    args = parser.parse_args()

    if args.url:
        logging.log(logging.INFO, "Processing one specified URL...")
        page = CleanHtml(args.url)
        page.process(dest=args.savefile)
    elif args.urlfile:
        logging.log(logging.INFO, "Processing URL list from file...")

        try:
            # TODO: Maybe move read link list to class?
            with open(args.urlfile, 'r') as urllist:
                for link in urllist:
                    page = CleanHtml(link)
                    page.process()
        except IOError:
            print("URL list read error!")
    else:
        print("Please, enter URL")
        sys.exit(1)