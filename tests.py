import re
import unittest
from os import path

from mwapi import LearnersDictionary, WordNotFoundException

class LearnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_key = ""

    def test_word_not_found(self):
        d = LearnersDictionary(self.api_key)
        with self.assertRaises(WordNotFoundException):
            try:
                list(d.lookup("murda"))
            except WordNotFoundException as e:
                self.assertTrue(len(e.suggestions) > 0)
                raise e

    def test_handle_malformed_xml(self):
        d = LearnersDictionary(self.api_key)
        with self.assertRaisesRegexp(WordNotFoundException,
                                     r'.* not found\.( Try:.*)?$'):
            list(d.lookup("3rd"))

if __name__ == '__main__':
    unittest.main()
