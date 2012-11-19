import re
import xml.etree.cElementTree as ElementTree

from abc import ABCMeta, abstractmethod
from urllib import quote, quote_plus
from urllib2 import urlopen

"""
undocumented: subj, formula, table

<!ELEMENT entry (((subj?, art?, formula?, table?),
                  hw, (pr?, pr_alt?, pr_ipa?, pr_wod?, sound?)*,
                  (ahw, (pr, pr_alt?, pr_ipa?, pr_wod?, sound?)?)*, vr?),
                 (fl?, in*, lb*, ((cx, (ss | us)h*) | et)*, sl*),
                 (dx | def)*, (list? | (uro*, dro*,
                               ((pl, pt, sa?)|(note)|quote+)*))
                 )>

<!ATTLIST entry
	id CDATA #REQUIRED
	printing CDATA #IMPLIED
	rating CDATA #IMPLIED
>
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

class MWApiWrapper:
    """ Defines an interface for wrappers to Merriam Webster web APIs. """

    __metaclass__ = ABCMeta

    def __init__(self, key=None):
        self.key = key

    @abstractmethod
    def request_url(self, *args):
        """   """
        pass

    def stringify_tree(self, root, test=None):
        """ Returns concatenation of node.text and node.tail for all nodes in
        root.

        test is a function accepting a single node as an argument and returning
        a boolean indicating whether or not this node should be included in the
        output.

        """

        parts = [root.text] if root.text else []
        for node in root:
            if test and not test(node):
                continue
            for p in [node.text, node.tail]:
                if p:
                    parts.append(p)
        return ''.join(parts).strip()

class LearnersDictionary(MWApiWrapper):
    def lookup(self, word):
        response = urlopen(self.request_url(word))
        data = response.read()
        root = ElementTree.fromstring(data)
        entries = root.findall("entry")
        if not entries:
            suggestions = root.findall("suggestion")
            if suggestions:
                suggestions = [s.text for s in suggestions]
            raise WordNotFoundException(word, suggestions)
        for num, entry in enumerate(entries):
            args = {}
            args['headword'] = entry.find("hw").text
            sound = entry.find("sound")
            if sound:
                args['sound_fragments'] = [s.text for s in sound]
            args['functional_label'] = entry.find('fl').text
            args['senses'] = []
            for definition in entry.findall('.//def/dt'):
                dstring = self.stringify_tree(definition,
                              lambda x: x.tag not in ['vi', 'wsgram', 'un', 'dx'])
                dstring = re.sub("^:", "", dstring)
                dstring = re.sub(r'(\s*):', r';\1', dstring)
                usage = [self.vi_to_text(u) for u in definition.findall('.//vi')]
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
        self.functional_label = attrs.get("functional_label")
        # aka pos?
        self.inflections = attrs.get("inflections") # (form, [pr], note,)
        self.senses = attrs.get("senses")
        # list of (["def text"], ["examples"], ["notes"])
        sound_fragments = attrs.get("sound_fragments")
        art_fragment = attrs.get("art_fragment")
