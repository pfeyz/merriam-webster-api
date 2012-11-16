from abc import ABCMeta, abstractmethod, abstractproperty

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

class MWApi:
    """ Defines an interface for wrappers to Merriam Webster web APIs. """

    __metaclass__ = ABCMeta

    @abstractmethod
    def request_url(self, *args):
        """   """
        pass

class LearnersDictionaryEntry(object):
    def __init__(self, attrs):
        # word,  pronounce, sound_url, art_url, inflection, pos

        self.headword = attrs.get("headword")
        self.alternate_headwords = attrs.get("alternate_headwords")
        self.pronunciations = attrs.get("pronunciations")
        self.functional_label = attrs.get("functional_label")
        # aka pos?
        self.inflections = attrs.get("inflections") # (form, [pr], note,)
        self.definitions = attrs.get("definitions")
        # list of (["def text"], ["examples"], ["notes"])
        sound_fragment = attrs.get("sound_fragment")
        art_fragment = attrs.get("art_fragment")
