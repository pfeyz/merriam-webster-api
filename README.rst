===================
Merriam-Webster API
===================

A wrapper around the Merriam-Webster APIs as Python module.

You'll need to get API keys from `Merriam-Webster's Developer Center`_.

Currently only the Learner's Dictionary is implemented. Support for the
Collegiate Dictionary and Thesaurus are planned, but note that Merriam-Webster's
`terms of service`_ forbid use of more than two of their reference works via the
APIs.

I was initially interested in the API for the IPA_ transcriptions that
Merriam-Webster provides. I targeted the Learner's Dictionary which uses IPA
unlike MW's Collegiate Dictionary which uses a `non-ipa pronunciation
notation`_.

See examples/ipa.py for an example script using the module to fetch IPA
transcriptions.

The example script and tests expect to find your Learner's Dictionary API key in
the ``MERRIAM_WEBSTER_LEARNERS_KEY`` environmental variable.


.. _`Merriam-Webster's Developer Center`: http://www.dictionaryapi.com/
.. _`terms of service`: http://www.dictionaryapi.com/info/terms-of-service.htm
.. _IPA: https://en.wikipedia.org/wiki/Ipa
.. _`non-ipa pronunciation notation`: http://en.wikipedia.org/wiki/Merriam-Webster#Pronunciation_guides
