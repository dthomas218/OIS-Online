## Controller Python Script "relative_path"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##parameters=
##title=Relative Path
##

from Products.CMFCore.utils import getToolByName
purl = getToolByName(context, 'portal_url')
return purl.getRelativeContentURL(context)
