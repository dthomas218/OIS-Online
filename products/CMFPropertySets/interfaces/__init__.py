# import this

from Products.PropertySets.interfaces.registry import IPropertySetRegistry

class ILocalVocabRegistry(IPropertySetRegistry):
    """Local Vocabulary Registry"""

class IGlobalVocabRegistry(ILocalVocabRegistry):
    """Global Vocabulary Registry"""
