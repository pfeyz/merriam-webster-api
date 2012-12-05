# -*- encoding: utf-8 -*-

"""
Simple command-line tool that fetches the dictionary definitions of a given word
from Merriam Webster.

  $ python define.py bike
  bike [noun]: bicycle
  bike [noun]: motorcycle
  bike [verb]: to ride a bicycle

  $ python define.py definition
  definition [noun]: an explanation of the meaning of a word, phrase, etc.; a statement that defines a word, phrase, etc.
  definition [noun]: a statement that describes what something is
  definition [noun]: a clear or perfect example of a person or thing
  definition [noun]: the quality that makes it possible to see the shape, outline, and details of something clearly

  $ python define.py refactor
  No definitions found for 'refactor'

"""

import os
import sys

from merriam_webster.api import LearnersDictionary, WordNotFoundException

if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    key = os.getenv("MERRIAM_WEBSTER_LEARNERS_KEY")  # gets your api key
    learners = LearnersDictionary(key)
    try:
        defs = [(entry.word, entry.function, definition)
                for entry in learners.lookup(query)
                for definition, examples in entry.senses
                # some senses will not have definitions, only usage examples.
                # also, the api will return related words different from what we
                # queried.
                if definition and entry.word == query]
    except WordNotFoundException:
        defs = []
    if defs == []:
        print "No definitions found for '{0}'".format(query)
    for word, pos, definition in defs:
        print "{0} [{1}]: {2}".format(word, pos, definition)
