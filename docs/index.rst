.. django-adminlinks documentation master file,
    created by sphinx-quickstart on Thu Sep 6 20:10:58 2012.

django-adminlinks
=================

Usage documentation
-------------------

.. toctree::
    :maxdepth: 5

    getting_started
    extras

What it is
----------

A suite of template tags for rendering links to a Django
:class:`~django.contrib.admin.AdminSite` instance.

At it's most basic, given a :class:`~django.db.models.Model`, it will do the
appropriate checks to ensure that the currently signed in user can perform the
requested action via the admin, and displays a configurable template with a link
to the right place.

Why?
----

Because I wedge the Django admin into everything, whether it should fit or not.
Not so much because I love the admin, but because it provides a well-understood
CRUD application that can be bolted onto in a pinch.

Features
--------

Here's a brief run-down on what's in the box:

* Basic, sane permission checking

  * Calling the template tags without a RequestContext should not expose any
    markup.
  * Users must be signed in, and pass the permission checking for
    the specific administration view.

* Optional :ref:`CSS <bundled_css>` and :ref:`JavaScript <bundled_js>` to
  improve the functionality by
  :ref:`providing "button" like links <preview_buttons>`, and a modal window
  for opening links.
* Pretty reasonable documentation. Or at least that's the aim.
* An additional view on all instances which subclass our
  :class:`~adminlinks.admin.AdminlinksMixin`, to edit
  a specific field on a model, which can be used for some fairly neat in-place
  editing of only distinct parts of some data.


API information (auto-generated)
--------------------------------

.. toctree::
    :maxdepth: 3

    api/templatetags
    api/admin
    api/views
    api/utils
    api/constants

.. _contributing:

Contributing
------------

Please do!

The project is hosted on `GitHub`_ in the `kezabelle/django-adminlinks`_
repository. The main branch is *master*.

Bug reports and feature requests can be filed on the repository's `issue tracker`_.

If something can be discussed in 140 character chunks, there's also `my Twitter account`_.

Similar projects
----------------

In the course of writing this, I have become aware of other packages tackling
the same sort of thing:

* `Martin Mahner's django-frontendadmin`_
* `Yaco Sistemas' django-inplaceedit`_
* `Ryan Berg's django-jumptoadmin`_
* `Maxime Haineault's django-editlive`_
* `Interaction Consortium's django-adminboost`_

If you're aware of any others working in the same space, let me know and I'll
add them here.

.. _GitHub: https://github.com/
.. _kezabelle/django-adminlinks: https://github.com/kezabelle/django-adminlinks/
.. _issue tracker: https://github.com/kezabelle/django-adminlinks/issues/
.. _my Twitter account: https://twitter.com/kezabelle/
.. _Martin Mahner's django-frontendadmin: https://github.com/bartTC/django-frontendadmin/
.. _Yaco Sistemas' django-inplaceedit: https://github.com/Yaco-Sistemas/django-inplaceedit/
.. _Ryan Berg's django-jumptoadmin: https://github.com/ryanberg/django-jumptoadmin/
.. _Maxime Haineault's django-editlive: https://github.com/h3/django-editlive/
.. _Interaction Consortium's django-adminboost: https://github.com/ixc/glamkit-adminboost/
