import zope.interface

class IPropertySetRegistry(zope.interface.Interface):

    def getPropSetsFor(obj):
        """Returns an iterable containing the property sets that apply
        to a specific object.
        """
