# -*- encoding: utf-8 -*-

"""
Simple command-line tool that fetches the dictionary definitions of a given word
from Merriam Webster.

  $ python define.py bike
  LEARNERS: bike [noun]: bicycle
  LEARNERS: bike [noun]: motorcycle
  LEARNERS: bike [verb]: to ride a bicycle
  COLLEGIATE: bike [noun]: a nest of wild bees, wasps, or hornets
  COLLEGIATE: bike [noun]: a crowd or swarm of people
  COLLEGIATE: bike [noun]: bicycle
  COLLEGIATE: bike [noun]: motorcycle
  COLLEGIATE: bike [noun]: motorbike
  COLLEGIATE: bike [noun]: stationary bicycle
  COLLEGIATE: bike [verb]: to ride a bike

  $ python define.py definition
  LEARNERS: definition [noun]: an explanation of the meaning of a word, phrase, etc.; a statement that defines a word, phrase, etc.
  LEARNERS: definition [noun]: a statement that describes what something is
  LEARNERS: definition [noun]: a clear or perfect example of a person or thing
  LEARNERS: definition [noun]: the quality that makes it possible to see the shape, outline, and details of something clearly
  COLLEGIATE: definition [noun]: an act of determining
  COLLEGIATE: definition [noun]: the formal proclamation of a Roman Catholic dogma
  COLLEGIATE: definition [noun]: a statement expressing the essential nature of something
  COLLEGIATE: definition [noun]: a statement of the meaning of a word or word group or a sign or symbol
  COLLEGIATE: definition [noun]: a product of defining
  COLLEGIATE: definition [noun]: the action or process of stating the meaning of a word or word group
  COLLEGIATE: definition [noun]: the action or the power of describing, explaining, or making definite and clear
  COLLEGIATE: definition [noun]: clarity of visual presentation; distinctness of outline or detail
  COLLEGIATE: definition [noun]: clarity especially of musical sound in reproduction
  COLLEGIATE: definition [noun]: sharp demarcation of outlines or limits
  COLLEGIATE: definition [adjective]: being or relating to an often digital television system that has twice as many scan lines per frame as a conventional system, a proportionally sharper image, and a wide-screen format
  COLLEGIATE: definition [noun]: the evaluation by oneself of one's worth as an individual in distinction from one's interpersonal or social roles


  $ python define.py refactor
  LEARNERS: No definitions found for 'refactor'
  COLLEGIATE: No definitions found for 'refactor'

"""

import os
import sys

from merriam_webster.api import (LearnersDictionary, CollegiateDictionary,
                                 WordNotFoundException)

def lookup(dictionary_class, key, query):
    dictionary = dictionary_class(key)
    try:
        defs = [(entry.word, entry.function, definition)
                for entry in dictionary.lookup(query)
                for definition, examples in entry.senses]
    except WordNotFoundException:
        defs = []
    dname = dictionary_class.__name__.replace('Dictionary', '').upper()
    if defs == []:
        print "{0}: No definitions found for '{1}'".format(dname, query)
    for word, pos, definition in defs:
        print "{0}: {1} [{2}]: {3}".format(dname, word, pos, definition)


if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    learnkey, collkey = (os.getenv("MERRIAM_WEBSTER_LEARNERS_KEY"),
                         os.getenv("MERRIAM_WEBSTER_COLLEGIATE_KEY"))
    if not (learnkey or collkey):
        print ("set the MERRIAM_WEBSTER_LEARNERS_KEY and/or MERRIAM_WEBSTER_"
               "COLLEGIATE_KEY environmental variables to your Merriam-Webster "
               "API keys in order to perform lookups.")
    if learnkey:
        lookup(LearnersDictionary, learnkey, query)
    if collkey:
        lookup(CollegiateDictionary, collkey, query)
