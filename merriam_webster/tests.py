# -*- encoding: utf-8 -*-

import re
import unittest
import urllib2
from os import path, getenv

from api import (LearnersDictionary, CollegiateDictionary,
                 WordNotFoundException, InvalidAPIKeyException)

TEST_DIR = path.dirname(__file__)

class MerriamWebsterTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ Sets class api_key, data_dir and request_prefix class variables.

        Assumes the `Name` portion of `NameTests` will work for all three
        variables.
        """

        name = re.sub(r'Tests$', '', cls.__name__).lower()
        cls.api_key = getenv('MERRIAM_WEBSTER_{0}_KEY'.format(name.upper()))
        cls.data_dir = path.join(TEST_DIR, 'test_data', name)
        cls.request_prefix = ('http://www.dictionaryapi.com/api/v1/references/'
                              '{0}/xml/').format(name)

    def setUp(self):
        """ Initializes dictionary instance variable that uses the mocked
        urlopen funciton.

        """
        self.dictionary = self.dict_class(self.api_key,
                                          self._cached_url_opener())

    def _cached_url_opener(self):
        """ Mocks urllib2.urlopen.

        Returns a function which returns cached-to-disk MW data.

        If no xml test data is found, it's fetched from MW. This allows us to
        run lots of tests without worrying about surpassing the 1000 req/day API
        limit while avoiding copyright infringement by not distributing MW's
        data with this codebase.

        """
        def opener(url):
            fn = re.sub(r"^%s" % self.request_prefix, "", url)
            fn = re.sub(r"\?.*$", "", fn)  # strip api key
            fn = path.join(self.data_dir, "{0}.xml".format(fn))
            try:
                return open(fn, 'r')
            except IOError:
                data = urllib2.urlopen(url)
                with open(fn, 'w') as fh:
                    fh.write(data.read())
                return open(fn, 'r')
        return opener


class LearnersTests(MerriamWebsterTestCase):

    dict_class = LearnersDictionary

    def test_attribute_parsing(self):
        entries = list(self.dictionary.lookup("pirate"))
        self.assertEqual(2, len(entries))
        first_entry = entries[0]
        self.assertEqual("pirate", first_entry.word)
        self.assertEqual("pi*rate", first_entry.headword)
        self.assertEqual("noun", first_entry.function)
        self.assertEqual(u"ˈpaɪrət", first_entry.pronunciations[0])
        senses = list(first_entry.senses)
        self.assertEqual(3, len(senses))

        inflections = list(first_entry.inflections)
        self.assertEquals(1, len(inflections))
        self.assertEquals(inflections[0].label,
                          "plural")
        self.assertEquals(inflections[0].forms,
                          ["pi*rates"])

        sense = senses[0]
        definition, examples = sense
        self.assertTrue(
            definition.startswith("someone who attacks and steals"))
        self.assertEqual(2, len(examples))

        sense = senses[1]
        self.assertTrue(
            sense.definition.startswith("someone who illegally copies"))
        self.assertEqual(3, len(sense.examples))

        entries = list(self.dictionary.lookup("starfish"))
        starfish = entries[0]
        inflections = list(starfish.inflections)
        self.assertEquals(1, len(inflections))
        self.assertEquals('plural', inflections[0].label)
        self.assertEquals('star*fish', inflections[0].forms[0])
        self.assertEquals('star*fish*es', inflections[0].forms[1])
        self.assertEquals('noun', starfish.function)
        self.assertEquals("www.learnersdictionary.com/art/ld/starfish.gif",
                          starfish.illustrations[0])
        self.assertEquals(
            "http://media.merriam-webster.com/soundc11/s/starfi01.wav",
            starfish.audio[0])
        senses = list(starfish.senses)
        self.assertEquals(1, len(senses))
        self.assertTrue(senses[0].definition.startswith('a sea animal'))

    def test_word_not_found(self):
        with self.assertRaises(WordNotFoundException):
            try:
                list(self.dictionary.lookup("murda"))
            except WordNotFoundException as e:
                self.assertTrue(len(e.suggestions) > 0)
                raise e

    def test_handle_malformed_xml(self):
        with self.assertRaisesRegexp(WordNotFoundException,
                                     r'.* not found\.( Try:.*)?$'):
            list(self.dictionary.lookup("3rd"))


class CollegiateTests(MerriamWebsterTestCase):

    dict_class = CollegiateDictionary

    def test_lookup(self):
        list(self.dictionary.lookup("test"))
        list(self.dictionary.lookup("resume"))
        with self.assertRaises(WordNotFoundException):
            list(self.dictionary.lookup("wooza"))
        with self.assertRaises(InvalidAPIKeyException):
            d = self.dict_class(self.api_key + 'zzz')
            list(d.lookup("something"))
        with self.assertRaises(InvalidAPIKeyException):
            d = self.dict_class(None)
            list(d.lookup("anything"))

    def test_handle_malformed_xml(self):
        with self.assertRaisesRegexp(WordNotFoundException,
                                     r'.* not found\.( Try:.*)?$'):
            list(self.dictionary.lookup("3rd"))

    def test_attribute_parsing(self):
        results = list(self.dictionary.lookup('spry'))
        self.assertEquals(len(results), 3)
        entry = results[0]
        self.assertEquals('spry', entry.word)
        self.assertEquals('spry', entry.headword)
        self.assertEquals('adjective', entry.function)
        self.assertEquals(u"ˈsprī", entry.pronunciations[0])
        inflections = list(entry.inflections)
        self.assertEquals(2, len(inflections))
        for expected, observed in zip([['spri*er', 'spry*er'],
                                       ['spri*est', 'spry*est']],
                                      inflections):
            self.assertEquals(expected, observed.forms)
        senses = list(entry.senses)
        self.assertEquals(len(senses), 1)
        sense = senses[0]
        self.assertEquals(sense.definition, 'nimble')
        self.assertEquals(sense.examples[0], 'a spry 75-year-old')

        self.assertEquals('sprier', results[1].headword)
        self.assertEquals('spriest', results[2].headword)

        results = list(self.dictionary.lookup("hack"))
        self.assertEquals(len(results), 7)
        self.assertEquals('verb', results[0].function)
        self.assertEquals('adjective', results[3].function)
        self.assertEquals('verb', results[5].function)
        self.assertEquals(
            "http://media.merriam-webster.com/soundc11/s/spry0001.wav",
            entry.audio[0])

        entry = results[0]
        self.assertEquals('hack', entry.word)
        self.assertEquals('verb', entry.function)
        self.assertEquals(u"ˈhak", entry.pronunciations[0])
        for e in results[1:]:
            self.assertEquals([], e.pronunciations)
        senses = list(entry.senses)
        self.assertEquals(13, len(senses))

        self.assertTrue(senses[0].definition.startswith('to cut or sever'))
        self.assertTrue(senses[1].definition.startswith('to cut or shape'))
        self.assertEquals('annoy vex', senses[2].definition)
        self.assertTrue(senses[1].examples[0] == \
                            'hacking out new election districts')
        self.assertTrue(senses[6].definition.startswith('to make chopping'))
        self.assertTrue(senses[6].examples[0].startswith('hacked at'))
        self.assertTrue(senses[7].definition.startswith('to make cuts as if'))
        self.assertTrue(senses[7].examples[0].startswith('hacking away at'))
        self.assertEquals(
            "http://media.merriam-webster.com/soundc11/h/hack0001.wav",
            entry.audio[0])

        entry = results[2]
        self.assertEquals('hack', entry.word)
        self.assertEquals('noun', entry.function)
        senses = list(entry.senses)
        self.assertEquals(len(senses), 13)

        sense = senses[5]
        self.assertEquals(sense.definition, 'a horse worn out in service; jade')

        results = list(self.dictionary.lookup('heart'))
        self.assertEquals('http://www.merriam-webster.com/art/dict/heart.htm',
                          results[0].illustrations[0],)

if __name__ == '__main__':
    unittest.main()
