"""
Simple command-line tool that fetches the IPA (International Phonetic Alphabet)
transcriptions for a given word from Merriam Webster.

  $ python2 ipa.py tomato
  təˈmeɪtoʊ
  təˈmɑ:təʊ

  $ python2 ipa.py xml
  ˌɛksˌɛmˈɛl

For simplicities sake, WordNotFound exceptions thrown by
LearnersDictionary.lookup are not handled.

"""

import os
import sys

from merriam_webster.api import LearnersDictionary

if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    key = os.getenv("MERRIAM_WEBSTER_LEARNERS_KEY")  # gets your api key
    learners = LearnersDictionary(key)
    ipas = [ipa
            for entry in learners.lookup(query)
            for ipa in entry.pronunciations]
    for ipa in set(ipas):
        print ipa
    if not ipas:
        print "No transcriptions found for '{0}'".format(query)
