=======
DavPack
=======

A set of patches for all things related to WebDAV
=================================================

:Author: Sidnei da Silva
:Contact: sidnei@enfoldsystems.com
:Date: $Date: 2004-10-11 11:18:09 -0300 (Mon, 11 Oct 2004) $
:Version: $Revision: 1.1 $

Yes, it's me again, fixing WebDAV.

This product aims to be a drop-in product to be installed on your Zope
and that will monkeypatch some methods to make Zope (and Zope-based
products, including Archetypes) more memory friendly when uploading
large files.

Installation
============

Just drop it in your Products directory and restart. When the related
products start including the patches, we will warn you so that you can
remove it.


Here's a in-depth description about the issue:

- The whole samba starts in ``ZServer/HTTPServer.py``,
  ``zhttp_collector``.

  + If the request size (?) is bigger than ``524288`` bytes (?) it
    uses a ``TemporaryFile`` to store the request data. Otherwise, it
    uses a ``cStringIO.StringIO``. Fair enough, though I suppose that
    threshold could be smaller.

- However, it just uses ``zhttp_collector`` if a ``CONTENT_LENGTH``
  header is found! (``zhttp_handler.handle_request``)

- That suggests that if the client (in our case ``davlib.py``) doesn't
  set ``Content-Length``, a ``cStringIO.StringIO`` will be blindly
  created.

- ``davlib.py`` (at least our modified version) seems to set
  ``Content-Length`` properly (and so does ``cadaver``), so Zope is
  creating a temporary file as expected.

- The next thing that happens is that the request is passed through
  ``cgi.FieldStorage``, which creates **yet another** temporary file
  by reading the one ``zhttp_collector`` had created. This far,
  nothing read the whole file in memory, which is cool.

- Next thing is traversing to a resource and calling it's ``PUT``
  method.

  + If the resource doesn't yet exists:

    * A ``webdav.NullResource`` object is created, and it's ``PUT``
      method is called.

    * It looks for a ``Content-Type`` header on the request. If that's
      not found, it tries to guess the content type from the
      filename. If that doesn't happen, it tries a ``re.search`` to
      figure out if its a binary file. Humm... which seems like it
      will fail if the uploaded file is big as it will receive a file
      object here??

    * ``PUT`` looks for a ``PUT_factory`` method on the parent object,
      and if that's not found, it uses
      ``NullResource._default_PUT_factory``, which will:

       + Create a ``ZopePageTempate`` for a file ending with ``.pt``

       + Create a ``DTMLDocument`` for anything with content-type of
         ``text/html``, ``text/xml`` or ``text/plain``

       + Create a ``OFS.Image`` for anything with content-type
         ``image/*``

       + Create a ``OFS.File`` for anything else.

    * When inside CMF/Plone, ``PortalFolder`` implements
      ``PUT_factory`` and delegates to ``content_type_registry``. That
      one **may** be reading the whole file in memory. Add note to
      check later.

  + After ``PUT_factory`` is called, everything behaves as if the file
    already existed.

  + The next step is delegating to the existing resource, or
    newly-created object ``PUT`` method.

  + When using ``OFS.File``, Zope seems to behave exceptionally
    well. Here's what happens:

    * The request body is read in 64K chunks into a linked list of
      ``Pdata`` objects.

    * The ``Pdata`` objects get a ``_p_jar`` immediately, and a
      subtransaction is triggered.

    * As the subtransaction is triggered, a ``TmpStore`` object is
      created to hold the transaction data temporarily.

    * The ``TmpStore`` creates **yet another** temporary file.

    * When the real transaction is commited, all the info on the
      ``TmpStore`` is copied over to the real storage.

**Conclusion so far**: Zope seems to be able to handle large files
correctly out of the box. The problem may lie somewhere inside
CMF/Plone.

**Update**: Found two places where Zope was reading the whole file in
memory.

+ ``NullResource.PUT`` does a ``REQUEST.get('BODY', '')``, which reads the
  file into a string, thus loading the whole thing in memory.

+ Still in ``NullResource.PUT``, **after** the object is created but
  **before** it is stitched into the storage, the ``PUT`` method for
  the object is called. ``OFS.File`` though reads **the whole file**
  into a single ``Pdata`` object if a ``_p_jar`` is not found.

