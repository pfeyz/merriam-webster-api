===================
Merriam-Webster API
===================

A wrapper around the Merriam-Webster APIs as Python module.

You'll need to get API keys from `Merriam-Webster's Developer Center`_.

The Learner's Dictionary is supported and there is a preliminary implementation
of the Collegiate Dictionary. Support for the Thesaurus is planned, but note
that Merriam-Webster's `terms of service`_ forbid use of more than two of their
reference works via the APIs.

I was initially interested in the API for the IPA_ transcriptions that
Merriam-Webster provides. I started with the Learner's Dictionary which uses IPA
unlike MW's Collegiate Dictionary which uses a `non-ipa pronunciation
notation`_.

See examples/ for usage examples.

The example scripts and tests expect to find your API keys in the
``MERRIAM_WEBSTER_LEARNERS_KEY`` and/or ``MERRIAM_WEBSTER_COLLEGIATE_KEY``
environmental variables.


.. _`Merriam-Webster's Developer Center`: http://www.dictionaryapi.com/
.. _`terms of service`: http://www.dictionaryapi.com/info/terms-of-service.htm
.. _IPA: https://en.wikipedia.org/wiki/Ipa
.. _`non-ipa pronunciation notation`: http://en.wikipedia.org/wiki/Merriam-Webster#Pronunciation_guides
