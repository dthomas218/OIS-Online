from Interface import Interface

class IPropertySetPredicate(Interface):

    def apply(obj):
        """Return the PropertySets that apply to the given object
        after satisfying the predicate conditions
        """

