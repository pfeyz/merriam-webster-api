# -*- encoding: utf-8 -*-

import re
import xml.etree.cElementTree as ElementTree

from abc import ABCMeta, abstractmethod, abstractproperty
from urllib import quote, quote_plus
from urllib2 import urlopen

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

class InvalidAPIKeyException(Exception):
    pass

class MWApiWrapper:
    """ Defines an interface for wrappers to Merriam Webster web APIs. """

    __metaclass__ = ABCMeta

    def __init__(self, key=None, urlopen=urlopen):
        """ key is the API key string to use for requests. urlopen is a function
        that accepts a url string and returns a file-like object of the results
        of fetching the url. defaults to urllib2.urlopen, and should throw """
        self.key = key
        self.urlopen = urlopen

    @abstractproperty
    def base_url():
        """ The api enpoint url without trailing slash or format (/xml).

        """
        pass

    @abstractmethod
    def parse_xml(root, word):
        pass

    def request_url(self, word):
        """ Returns the target url for an API GET request (w/ API key).

        >>> class MWDict(MWApiWrapper):
        ...     base_url = "mw.com/my-api-endpoint"
        ...     def parse_xml(): pass
        >>> MWDict("API-KEY").request_url("word")
        'mw.com/my-api-endpoint/xml/word?key=API-KEY'

        Override this method if you need something else.
        """

        if self.key is None:
            raise InvalidAPIKeyException("API key not set")
        qstring = "{0}?key={1}".format(quote(word), quote_plus(self.key))
        return ("{0}/xml/{1}").format(self.base_url, qstring)

    def lookup(self, word):
        response = self.urlopen(self.request_url(word))
        data = response.read()
        try:
            root = ElementTree.fromstring(data)
        except ElementTree.ParseError:
            if re.search("Invalid API key", data):
                raise InvalidAPIKeyException()
            data = re.sub(r'&(?!amp;)', '&amp;', data)
            try:
                root = ElementTree.fromstring(data)
            except ElementTree.ParseError:
                raise InvalidResponseException(word)

        suggestions = root.findall("suggestion")
        if suggestions:
            suggestions = [s.text for s in suggestions]
            raise WordNotFoundException(word, suggestions)

        return self.parse_xml(root, word)

    def _flatten_tree(self, root, exclude=None):
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

    def _stringify_tree(self, *args, **kwargs):
        " Returns a string of the concatenated results from _flatten_tree "
        return ''.join(self._flatten_tree(*args, **kwargs))

class LearnersDictionary(MWApiWrapper):

    base_url = "http://www.dictionaryapi.com/api/v1/references/learners"

    def parse_xml(self, root, word):
        entries = root.findall("entry")
        for num, entry in enumerate(entries):
            args = {}
            args['illustration_fragments'] = [e.get('id') for e in
                                     entry.findall("art/artref")
                                     if e.get('id')]
            args['headword'] = entry.find("hw").text
            args['pronunciations'] = self._get_pronunciations(entry)
            sound = entry.find("sound")
            args['sound_fragments'] = []
            if sound:
                args['sound_fragments'] = [s.text for s in sound]
            args['functional_label'] = getattr(entry.find('fl'), 'text', None)
            args['inflections'] = self._get_inflections(entry)
            args['senses'] = self._get_senses(entry)
            yield LearnersDictionaryEntry(
                re.sub(r'(?:\[\d+\])?\s*', '', entry.get('id')),
                       args)

    def _get_inflections(self, root):
        """ Returns a generator of Inflections found in root.

        inflection nodes that have <il>also</il> will have their inflected form
        added to the previous inflection entry.

        """
        for node in root.findall("in"):
            label, forms = None, []
            for child in node:
                if child.tag == 'il':
                    if child.text == 'also':
                        pass  # next form will be added to prev inflection-list
                    else:
                        if label is not None or forms != []:
                            yield Inflection(label, forms)
                        label, forms = child.text, []
                if child.tag == 'if':
                    forms.append(child.text)
            if label is not None or forms != []:
                yield Inflection(label, forms)

    def _get_pronunciations(self, root):
        """ Returns list of IPA for regular and 'alternative' pronunciation. """
        prons = root.find("./pr")
        pron_list = []
        if prons is not None:
            ps = self._flatten_tree(prons, exclude=['it'])
            pron_list.extend(ps)
        prons = root.find("./altpr")
        if prons is not None:
            ps = self._flatten_tree(prons, exclude=['it'])
            pron_list.extend(ps)
        return [p.strip(', ') for p in pron_list]

    def _get_senses(self, root):
        """ Returns a generator yielding tuples of definitions and example
        sentences: (definition_string, list_of_usage_example_strings). Each
        tuple should represent a different sense of the word.

        """
        for definition in root.findall('./def/dt'):
            # could add support for phrasal verbs here by looking for
            # <gram>phrasal verb</gram> and then looking for the phrase
            # itself in <dre>phrase</dre> in the def node or its parent.
            dstring = self._stringify_tree(definition,
                                          exclude=['vi', 'wsgram',
                                                   'ca', 'dx', 'snote',
                                                   'un'])
            dstring = re.sub("^:", "", dstring)
            dstring = re.sub(r'(\s*):', r';\1', dstring).strip()
            if not dstring:  # use usage note instead
                un = definition.find('un')
                if un is not None:
                    dstring = self._stringify_tree(un, exclude=['vi'])
            usage = [self._vi_to_text(u).strip()
                     for u in definition.findall('.//vi')]
            yield WordSense(dstring, usage)

    def _vi_to_text(self, root):
        example = self._stringify_tree(root)
        return re.sub(r'\s*\[=.*?\]', '', example)

class Inflection(object):
    def __init__(self, label, forms):
        self.label = label
        self.forms = forms

class WordSense(object):
    def __init__(self, definition, examples):
        self.definition = definition
        self.examples = examples

    def __str__(self):
        return "{0}, ex: [{1}]".format(self.definition[:30],
                                    ", ".join(i[:15] for i in self.examples))
    def __repr__(self):
        return "WordSense({0})".format(self.__str__())

    def __iter__(self):
        yield self.definition
        yield self.examples

class MWDictionaryEntry(object):
    def build_sound_url(self, fragment):
        base_url = "http://media.merriam-webster.com/soundc11"
        prefix_match = re.search(r'^([0-9]+|gg|bix)', fragment)
        if prefix_match:
            prefix = prefix_match.group(1)
        else:
            prefix = fragment[0]
        return "{0}/{1}/{2}".format(base_url, prefix, fragment)


class LearnersDictionaryEntry(MWDictionaryEntry):
    def __init__(self, word, attrs):
        # word,  pronounce, sound_url, art_url, inflection, pos

        self.word = word
        self.headword = attrs.get("headword")
        self.alternate_headwords = attrs.get("alternate_headwords")
        self.pronunciations = attrs.get("pronunciations")
        self.function = attrs.get("functional_label")
        self.inflections = attrs.get("inflections") # (form, [pr], note,)
        self.senses = attrs.get("senses")  # list of ("def text", ["examples"]
        self.audio = [self.build_sound_url(f) for f in
                      attrs.get("sound_fragments")]
        self.illustrations = [self.build_illustration_url(f) for f in
                              attrs.get("illustration_fragments")]

    def build_illustration_url(self, fragment):
        base_url = "www.learnersdictionary.com/art/ld"
        fragment = re.sub(r'\.(tif|eps)', '.gif', fragment)
        return "{0}/{1}".format(base_url, fragment)

class CollegiateDictionaryEntry(MWDictionaryEntry):
    def __init__(self, word, attrs):
        self.word = word
        self.headword = attrs.get('headword')
        self.function = attrs.get('functional_label')
        self.pronunciations = attrs.get("pronunciations")
        self.inflections = attrs.get("inflections")
        self.senses = attrs.get("senses")
        self.audio = [self.build_sound_url(f) for f in
                      attrs.get("sound_fragments")]
        self.illustrations = [self.build_illustration_url(f) for f in
                              attrs.get("illustration_fragments")]


    def build_illustration_url(self, fragment):
        base_url = 'http://www.merriam-webster.com/art/dict'
        fragment = re.sub(r'\.(bmp)', '.htm', fragment)
        return "{0}/{1}".format(base_url, fragment)


"""
<!ELEMENT entry
  (((subj?, art?, formula?, table?),
        hw,
        (pr?, pr_alt?, pr_ipa?, pr_wod?, sound?)*,
        (ahw, (pr, pr_alt?, pr_ipa?, pr_wod?, sound?)?)*,
        vr?),
     (fl?, in*, lb*, ((cx, (ss | us)*) | et)*, sl*),
     (dx | def)*,
     (list? |
       (uro*, dro*, ((pl, pt, sa?) |
                      (note) |
                      quote+)*)))>

"""


class CollegiateDictionary(MWApiWrapper):
    base_url = "http://www.dictionaryapi.com/api/v1/references/collegiate"

    def parse_xml(self, root, word):
        for entry in root.findall('entry'):
            args = {}
            args['headword'] = entry.find('hw').text
            args['functional_label'] = getattr(entry.find('fl'), 'text', None)
            args['pronunciations'] = self._get_pronunciations(entry)
            args['inflections'] = self._get_inflections(entry)
            args['senses'] = self._get_senses(entry)
            args['sound_fragments'] = []
            args['illustration_fragments'] = [e.text for e in
                                              entry.findall("art/bmp")
                                              if e.text]
            sound = entry.find("sound")
            if sound:
                args['sound_fragments'] = [s.text for s in sound]
            yield CollegiateDictionaryEntry(word, args)

    def _get_pronunciations(self, root):
        """ Returns list of IPA for regular and 'alternative' pronunciation. """
        prons = root.find("./pr")
        pron_list = []
        if prons is not None:
            ps = self._flatten_tree(prons, exclude=['it'])
            pron_list.extend(ps)
        return pron_list

    def _get_inflections(self, root):
        """ Returns a generator of Inflections found in root.

        inflection nodes that have <il>also</il> will have their inflected form
        added to the previous inflection entry.

        """
        for node in root.findall("in"):
            label, forms = None, []
            for child in node:
                if child.tag == 'il':
                    if child.text in ['also', 'or']:
                        pass  # next form will be added to prev inflection-list
                    else:
                        if label is not None or forms != []:
                            yield Inflection(label, forms)
                        label, forms = child.text, []
                if child.tag == 'if':
                    forms.append(child.text)
            if label is not None or forms != []:
                yield Inflection(label, forms)

    """

    <!ELEMENT def (vt?, date?, sl*, sense, ss?, us?)+ >

    <!ELEMENT sense (sn?,
                    (sp, sp_alt?, sp_ipa?, sp_wod?, sound?)?,
                    svr?, sin*, slb*, set?, ssl*, dt*,
                    (sd, sin?,
                      (sp, sp_alt?, sp_ipa?, sp_wod?, sound?)?,
                    slb*, ssl*, dt+)?)>
    """

    def _get_senses(self, root):
        """ Returns a generator yielding tuples of definitions and example
        sentences: (definition_string, list_of_usage_example_strings). Each
        tuple should represent a different sense of the word.

        """
        for definition in root.findall('./def/dt'):
            # could add support for phrasal verbs here by looking for
            # <gram>phrasal verb</gram> and then looking for the phrase
            # itself in <dre>phrase</dre> in the def node or its parent.
            dstring = self._stringify_tree(definition,
                                          exclude=['vi', 'wsgram',
                                                   'ca', 'dx', 'snote',
                                                   'un'])
            dstring = re.sub("^:", "", dstring)
            dstring = re.sub(r'(\s*):', r';\1', dstring).strip()
            if not dstring:  # use usage note instead
                un = definition.find('un')
                if un is not None:
                    dstring = self._stringify_tree(un, exclude=['vi'])
            usage = [self._vi_to_text(u).strip()
                     for u in definition.findall('.//vi')]
            yield WordSense(dstring, usage)

    def _vi_to_text(self, root):
        example = self._stringify_tree(root)
        return re.sub(r'\s*\[=.*?\]', '', example)
