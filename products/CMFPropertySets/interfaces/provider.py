from Interface import Interface, Attribute

class IVocabularyProvider(Interface):

    ns = Attribute('ns', 'Namespace for the target property')
    propid = Attribute('propid', 'Property Id for the target property')

    def getValueFor(obj):
        """ Return the vocab of allowed values
        for a given object.

        The vocab should be a XML string in the format:
        <term label='xxx' value='xxx' />
        <term label='yyy' value='yyy' />
        """
