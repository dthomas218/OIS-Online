Plone Hotfix for CVE 2011-0720
******************************

This is a critical security hotfix which should be applied to the following
versions of Plone:

* Plone 4 <= 4.0.3
* Plone 3 <= 3.3.5
* Any version of Plone 2.5, 2.1, or 2.0

Additional information about the hotfix including frequently asked questions
is available at http://plone.org/products/plone/security/advisories/cve-2011-0720

This hotfix applies the following modifications to improve Plone security:

* Applies security declarations to some methods that were missing them, in order
  to address the vulnerability identified in `CVE 2011-0720`_. The vulnerability
  discussed there affects Plone 2.5 and greater.
* Applies security declarations and removal of docstrings to some additional
  methods that were identified by the Plone security team in an audit following
  the identification of CVE 2011-0720. This includes some methods present in Plone
  2.0 and 2.1.
* If necessary, applies a patch to the ZPublisher to fix an issue with the checking
  of whether traversed methods are publishable. This issue affects Plone 3.0 and
  higher, and is also available in the following new Zope2 releases:
  2.10.13, 2.11.8, 2.12.15, 2.13.4

.. _`CVE 2011-0720`: http://web.nvd.nist.gov/view/vuln/detail?vulnId=CVE-2011-0720


Installation
============

Installation instructions can be found at
http://plone.org/products/plone-hotfix/releases/CVE-2011-0720

Changelog
=========

1.1 (2011-02-08)
----------------

- Try 2 ways to delete the docstring as we had one report of the way we were
  using not working (thanks Andrew Mleczko for the report).
  [davisagli]

- Fix issue with application to some recent revisions of Zope 2.10. Thanks to
  Ethan Jucovy for calling this to our attention.
  [davisagli]

1.0 (2011-02-08)
----------------

- Initial release
  [Plone security team]
