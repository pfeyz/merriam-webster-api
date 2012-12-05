# -*- encoding: utf-8 -*-

import re
import unittest
import urllib2
from os import path, getenv

from api import LearnersDictionary, WordNotFoundException

TEST_DIR = path.dirname(__file__)

class MerriamWebsterTestCase(unittest.TestCase):

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


class LearnerTests(MerriamWebsterTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_key = getenv("MERRIAM_WEBSTER_LEARNERS_KEY")
        cls.data_dir = path.join(TEST_DIR, "test_data", "learners")
        cls.request_prefix = \
            "http://www.dictionaryapi.com/api/v1/references/learners/xml/"

    def setUp(self):
        self.dictionary = LearnersDictionary(self.api_key,
                                             self._cached_url_opener())

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


if __name__ == '__main__':
    unittest.main()
