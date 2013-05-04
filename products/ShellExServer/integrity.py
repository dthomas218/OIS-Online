from base64 import b64encode
from StringIO import StringIO
from Acquisition import aq_inner
from ZPublisher.Publish import Retry

from zope.interface import classImplements
from plone.app.linkintegrity.interfaces import ILinkIntegrityInfo
from plone.app.linkintegrity.interfaces import ILinkIntegrityNotificationException
from plone.app.linkintegrity.exceptions import LinkIntegrityNotificationException
from plone.app.linkintegrity.browser.confirmation import RemoveConfirmationView

class ILinkIntegrityNotificationException2(ILinkIntegrityNotificationException):
    pass

classImplements(
    LinkIntegrityNotificationException, 
    ILinkIntegrityNotificationException2)

def env_name(name):
    name = ('_'.join(name.split("-"))).upper()
    if name[:5] != 'HTTP_':
        name = 'HTTP_%s' % name
    return name

class RemoveConfirmationView2(RemoveConfirmationView):

    X_CONFIRM = 'X-Link-Integrity-Confirm'
    X_CONFIRMED = 'X-Link-Integrity-Confirmed-Items'
    ENV_X_CONFIRM = env_name(X_CONFIRM)
    ENV_X_CONFIRMED = env_name(X_CONFIRMED)

    ERROR_MSG = ('<?xml version="1.0" encoding="utf-8"?>'
                 '<error>'
                 '<error_type>%s</error_type>'
                 '<error_value><![CDATA[%s]]></error_value>'
                 '</error>')

    def __call__(self):
        confirm = self.request.get_header(self.X_CONFIRM)
        confirmed = self.request.get_header(self.X_CONFIRMED)

        if confirm is not None:
            env = self.request._orig_env
            marker = ILinkIntegrityInfo(self.request).getEnvMarker()
            if confirm == 'ALL':
                env[marker] = 'all'
            else:
                assert confirmed
                env[marker] = confirmed
            if env.has_key(self.ENV_X_CONFIRM):
                del env[self.ENV_X_CONFIRM]
            if env.has_key(self.ENV_X_CONFIRMED):
                del env[self.ENV_X_CONFIRMED]
            raise Retry
            
        self.request.RESPONSE.setHeader(
            'X-Link-Integrity-Confirmed-Items',
            self.confirmedItems())
        ret = ['<integrity>',
               '<breaches>']
        for breach in self.integrityBreaches():
            ret.append('<item type="%s" title="%s" url="%s">' % (
                    breach['type'], breach['title'], breach['url']))
            ret.append('<sources>')
            for source in breach['sources']:
                ret.append('<item type="%s" title="%s" '
                           'url="%s" accessible="%s" />' %
                            (source.getPortalTypeName(),
                             source.title_or_id(),
                             source.absolute_url(),
                             self.isAccessible(source)))
            ret.append('</sources>')
            ret.append('</item>')
        ret.extend(['</breaches>',
                    '</integrity>'])
        return self.ERROR_MSG % ('LinkIntegrityNotificationException',
                                 ''.join(ret))
