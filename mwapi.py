# -*- encoding: utf-8 -*-

import re
import xml.etree.cElementTree as ElementTree

from abc import ABCMeta, abstractmethod
from urllib import quote, quote_plus
from urllib2 import urlopen

"""
undocumented: formula, table

<!ELEMENT entry ((art*, formula?, table?),
                  hw, hsl?, (pr | altpr)?,
                  (ahw, hsl?, (pr, altpr)?)*,
                  vr?, fl?, lb*, in*,
                  ((dx) | (cx?, def?))?,
                  dro*, dxnl*, uro*, syns*)>

TODO:

  - capture usage notes in a separate member var?

  - include uro (undefined runoff)? these appear to be variations on the entry
    word and have usage examples but no definitions.

  - Merriam Webster seems not to be encoding & correctly in their <suggestion>
    tags.

"""

class WordNotFoundException(KeyError):
    def __init__(self, word, suggestions=None, *args, **kwargs):
        self.word = word
        if suggestions is None:
            suggestions = []
        self.suggestions = suggestions
        message = "'{0}' not found.".format(word)
        if suggestions:
            message = "{0} Try: {1}".format(message, ", ".join(suggestions))
        KeyError.__init__(self, message, *args, **kwargs)

class InvalidResponseException(WordNotFoundException):
    def __init__(self, word, *args, **kwargs):
        self.word = word
        self.suggestions = []
        message = "{0} not found. (Malformed XML from server).".format(word)
        KeyError.__init__(self, message, *args, **kwargs)

class MWApiWrapper:
    """ Defines an interface for wrappers to Merriam Webster web APIs. """

    __metaclass__ = ABCMeta

    def __init__(self, key=None):
        self.key = key

    @abstractmethod
    def request_url(self, *args):
        """   """
        pass

    def flatten_tree(self, root, exclude=None):
        """ Returns a list containing the (non-None) .text and .tail for all
        nodes in root.

        exclude is a list of tag names whose text attributes should be
        excluded. their tails will still be included.

        """

        parts = [root.text] if root.text else []
        for node in root:
            targets = [node.tail]
            if not exclude or node.tag not in exclude:
                targets.insert(0, node.text)
            for p in targets:
                if p:
                    parts.append(p)
        return parts

    def stringify_tree(self, *args, **kwargs):
        " Returns a string of the concatenated results from flatten_tree "
        return ''.join(self.flatten_tree(*args, **kwargs))

class LearnersDictionary(MWApiWrapper):
    def lookup(self, word):
        response = urlopen(self.request_url(word))
        data = response.read()
        try:
            root = ElementTree.fromstring(data)
        except ElementTree.ParseError:
            data = re.sub(r'&(?!amp;)', '&amp;', data)
            try:
                root = ElementTree.fromstring(data)
            except ElementTree.ParseError:
                raise InvalidResponseException(word)
        entries = root.findall("entry")
        if not entries:
            suggestions = root.findall("suggestion")
            if suggestions:
                suggestions = [s.text for s in suggestions]
            raise WordNotFoundException(word, suggestions)
        for num, entry in enumerate(entries):
            args = {}
            args['headword'] = entry.find("hw").text
            prons = entry.find("./pr")
            pron_list = []
            if prons is not None:
                ps = self.flatten_tree(prons, exclude=['it'])
                pron_list.extend(ps)
            prons = entry.find("./altpr")
            if prons is not None:
                ps = self.flatten_tree(prons, exclude=['it'])
                pron_list.extend(ps)
            args['pronunciations'] = [p.strip(', ') for p in pron_list]
            sound = entry.find("sound")
            args['sound_fragments'] = []
            if sound:
                args['sound_fragments'] = [s.text for s in sound]
            try:
                args['functional_label'] = entry.find('fl').text
            except AttributeError:
                args['functional_label'] = None
            args['senses'] = []
            for definition in entry.findall('.//def/dt'):
                # could add support for phrasal verbs here by looking for
                # <gram>phrasal verb</gram> and then looking for the phrase
                # itself in <dre>phrase</dre> in the def node or its parent.
                dstring = self.stringify_tree(definition,
                                              exclude=['vi', 'wsgram',
                                                       'ca', 'dx', 'snote',
                                                       'un'])
                dstring = re.sub("^:", "", dstring)
                dstring = re.sub(r'(\s*):', r';\1', dstring)
                if not dstring:  # use usage note instead
                    un = definition.find('un')
                    if un is not None:
                        dstring = self.stringify_tree(un, exclude=['vi'])
                usage = [self.vi_to_text(u)
                         for u in definition.findall('.//vi')]
                args['senses'].append((dstring, usage))
            yield LearnersDictionaryEntry(word, args)

    def vi_to_text(self, root):
        example = self.stringify_tree(root)
        return re.sub(r'\s*\[=.*?\]', '', example)

    def request_url(self, word):
        if self.key is None:
            raise Exception("API key not set")
        qstring = "{0}?key={1}".format(quote(word), quote_plus(self.key))
        return ("http://www.dictionaryapi.com/api/v1/references/learners"
                "/xml/{0}").format(qstring)

class LearnersDictionaryEntry(object):
    def __init__(self, word, attrs):
        # word,  pronounce, sound_url, art_url, inflection, pos

        self.word = word
        self.headword = attrs.get("headword")
        self.alternate_headwords = attrs.get("alternate_headwords")
        self.pronunciations = attrs.get("pronunciations")
        self.function = attrs.get("functional_label")
        # aka pos?
        self.inflections = attrs.get("inflections") # (form, [pr], note,)
        self.senses = attrs.get("senses")
        # list of (["def text"], ["examples"], ["notes"])
        self.audio = [self.build_sound_url(f) for f in
                      attrs.get("sound_fragments")]
        art_fragment = attrs.get("art_fragment")

    def build_sound_url(self, fragment):
        base_url = "http://media.merriam-webster.com/soundc11"
        prefix_match = re.search(r'^([0-9]+|gg|bix)', fragment)
        if prefix_match:
            prefix = prefix_match.group(1)
        else:
            prefix = fragment[0]
        return "{0}/{1}/{2}".format(base_url, prefix, fragment)
