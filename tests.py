# -*- encoding: utf-8 -*-

import re
import unittest
from os import path, getenv

from mwapi import LearnersDictionary, WordNotFoundException

class MerriamWebsterTestCase(unittest.TestCase):
    def _mock_url_opener(self):
        def opener(url):
            fn = re.sub(r"^%s" % self.base_url, "", url)
            fn = re.sub(r"\?.*$", "", fn)
            fn = path.join(self.fixture_dir, "{0}.xml".format(fn))
            return open(fn, 'r')
        return opener

class LearnerTests(MerriamWebsterTestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_key = getenv("MERRIAM_WEBSTER_LEARNERS_KEY")
        cls.fixture_dir = "fixtures/learners"
        cls.base_url = \
            "http://www.dictionaryapi.com/api/v1/references/learners/xml/"

    def setUp(self):
        self.dictionary = LearnersDictionary(self.api_key,
                                             self._mock_url_opener())

    def test_attribute_parsing(self):
        entries = list(self.dictionary.lookup("pirate"))
        self.assertEqual(2, len(entries))
        entry = entries[0]
        self.assertEqual("pirate", entry.word)
        self.assertEqual("pi*rate", entry.headword)
        self.assertEqual("noun", entry.function)
        self.assertEqual(u"ˈpaɪrət", entry.pronunciations[0])
        senses = list(entry.senses)
        self.assertEqual(3, len(senses))

        inflections = list(entry.inflections)
        self.assertEquals(1, len(inflections))
        self.assertEquals(inflections[0].label,
                          "plural")
        self.assertEquals(inflections[0].form,
                          "pi*rates")
        self.assertEquals(0, len(inflections[0].pronunciations))

        sense = senses[0]
        definition, examples = sense
        self.assertTrue(
            definition.startswith("someone who attacks and steals"))
        self.assertEqual(2, len(examples))

        sense = senses[1]
        self.assertTrue(
            sense.definition.startswith("someone who illegally copies"))
        self.assertEqual(3, len(sense.examples))


    def test_word_not_found(self):
        with self.assertRaises(WordNotFoundException):
            try:
                list(self.dictionary.lookup("murda"))
            except WordNotFoundException as e:
                self.assertTrue(len(e.suggestions) > 0)
                raise e

    def test_handle_malformed_xmlq(self):
        with self.assertRaisesRegexp(WordNotFoundException,
                                     r'.* not found\.( Try:.*)?$'):
            list(self.dictionary.lookup("3rd"))

if __name__ == '__main__':
    unittest.main()
