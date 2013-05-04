import re
from Acquisition import aq_base
try:
    from Acquisition.interfaces import IAcquirer
    ZOPE_210 = False
except ImportError:
    # Zope < 2.12
    IAcquirer = None
    ZOPE_210 = True

from zExceptions import Forbidden, NotFound

from Products.PloneHotfix20110720 import logger

PATCHED_ZOPE_VERSIONS = {
    '10': 13, # 2.10.13
    '11': 8,  # 2.11.8
    '12': 15, # 2.12.15
    '13': 3,  # 2.13.3
    }

patch = True
try:
    import pkg_resources
    zope_version = pkg_resources.get_distribution('Zope2').version
except:
    # We can't determine the version, so we patch if possible
    logger.info('Cannot determine Zope version, attempting to patch DefaultPublishTraverse')
else:
    try:
        major, minor, sub = zope_version.split('.')
    except:
        logger.info('Cannot determine Zope version, attempting to patch DefaultPublishTraverse')
    else:
        major,minor,sub = zope_version.split('.')
        sub_match = re.match(r'^(\d+)', sub)
        sub_version = sub_match and int(sub_match.groups()[0])
        sub_patched = PATCHED_ZOPE_VERSIONS.get(minor, None)
        if sub_patched and sub_version >= sub_patched:
            logger.info('Zope version %s already contains DefaultPublishTraverse fix'%zope_version)
            patch = False


try:
    from ZPublisher.BaseRequest import DefaultPublishTraverse
    from ZPublisher.BaseRequest import typeCheck
except ImportError:
    # patch not needed in Zope 2.9
    DefaultPublishTraverse = None
else:
    from zope.component import queryMultiAdapter
    from zope.interface import Interface
    
    def publishTraverse(self, request, name):
        object = self.context
        URL=request['URL']

        if name[:1]=='_':
            raise Forbidden("Object name begins with an underscore at: %s" % URL)

        
        if hasattr(object,'__bobo_traverse__'):
            try:
                subobject=object.__bobo_traverse__(request, name)
                if type(subobject) is type(()) and len(subobject) > 1:
                    # If traversal returns a tuple treat it as a sequence
                    # of objects traversed over in the background
                    request['PARENTS'][-1:] = list(subobject[:-1])
                    object, subobject = subobject[-2:]            
            except (AttributeError, KeyError, NotFound), e:
                # Try to find a view
                subobject = queryMultiAdapter((object, request), Interface, name)                
                if subobject is not None:
                    # OFS.Application.__bobo_traverse__ calls
                    # REQUEST.RESPONSE.notFoundError which sets the HTTP
                    # status code to 404
                    request.response.setStatus(200)
                    # We don't need to do the docstring security check
                    # for views, so lets skip it and return the object here.
                    if ZOPE_210 or (IAcquirer and IAcquirer.providedBy(subobject)):
                        subobject = subobject.__of__(object)
                    return subobject
                # No view found. Reraise the error raised by __bobo_traverse__
                raise e
        else:
            # No __bobo_traverse__
            # Try with an unacquired attribute:
            if hasattr(aq_base(object), name):
                subobject = getattr(object, name)
            else:
                # We try to fall back to a view:
                subobject = queryMultiAdapter((object, request), Interface,
                                              name)
                if subobject is not None:
                    if ZOPE_210 or (IAcquirer and IAcquirer.providedBy(subobject)):
                        subobject = subobject.__of__(object)
                    return subobject
            
                # And lastly, of there is no view, try acquired attributes, but
                # only if there is no __bobo_traverse__:
                try:
                    subobject=getattr(object, name)
                    # Again, clear any error status created by __bobo_traverse__
                    # because we actually found something:
                    request.response.setStatus(200)
                except AttributeError:
                    pass

                # Lastly we try with key access:
                if subobject is None:
                    try:
                        subobject = object[name]
                    except TypeError: # unsubscriptable
                        raise KeyError(name)

        # Ensure that the object has a docstring. Objects that
        # have an empty or missing docstring are not published.
        doc = getattr(subobject, '__doc__', None)
        if not doc:
            raise Forbidden(
                "The object at %s has an empty or missing " \
                "docstring. Objects must have a docstring to be " \
                "published." % URL
                )

        if not typeCheck(subobject):
            raise Forbidden(
                "The object at %s is not publishable." % URL
                )

        return subobject


def install_patch():
    # patch publishTraverse
    if patch and DefaultPublishTraverse is not None:
        logger.info('Patching ZPublisher.DefaultPublishTraverse.publishTraverse')
        DefaultPublishTraverse.publishTraverse = publishTraverse
