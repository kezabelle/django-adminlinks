.. django-adminlinks documentation master file,
    created by sphinx-quickstart on Thu Sep 6 20:10:58 2012.

django-adminlinks
=================

.. toctree::
    :maxdepth: 2
    :titlesonly:

    getting_started
    extras
    under_the_hood

What it is
----------

A suite of template tags for rendering links to a Django
:django:class:`django.contrib.admin.sites.AdminSite` instance.

At it's most basic, given an object (a Django model), it will do the
appropriate checks to ensure that the currently signed in user can perform the
requested action via the admin.

It comes with :doc:`a few niceities <extras>`, none of which are required, and
a few configuration obstacles, which are. See the :doc:`getting started <getting_started>`
documentation for more details.

Why
---

Because I wedge the Django admin into everything, whether it should fit or not.
Not so much because I like the admin, but because it provides a well-understood
CRUD application that can be bolted onto in a pinch.

In many ways, it's like `Martin Mahner's django-frontendadmin`_, which does
much the same thing, though without re-using the Admin quite so completely.

.. _Martin Mahner's django-frontendadmin: https://github.com/bartTC/django-frontendadmin/
.. _Yaco Sistemas' django-inplaceedit: https://github.com/Yaco-Sistemas/django-inplaceedit/
Features
--------

Here's a brief run-down on what's in the box:

* Sane permission checking:

    * Calling the template tags without a RequestContext should not expose any
      markup.  * Users must be signed in, and pass the permission checking for
      the specific administration view.

* Bundled with a smattering of CSS and JavaScript to make things a bit better.
  Links are rendered in the same style as the admin form inputs, though without
  the use of any images.  JavaScript is provided to render the admin view
  'in-place' via an iframe modal, using the Admin in *popup* mode.
* Pretty reasonable documentation. Or at least that's the aim.
* An additional view on all instances which subclass our `ModelAdmin`, to edit
  a specific field on a model, which can beused for some fairly neat in-place
  editing of only distinct parts of some data.

.. _contributing:

Contributing
------------

Please do!

The project is hosted on `GitHub`_ in the `kezabelle/django-adminlinks`_
repository. The main branch is *master*, but all work is carried out on
*develop* and merged in.

Bug reports and feature requests can be filed on the repository's `issue tracker`_.

If something can be discussed in 140 character chunks, there's also `my Twitter account`_.

.. _GitHub: https://github.com/
.. _kezabelle/django-adminlinks: https://github.com/kezabelle/django-adminlinks/
.. _issue tracker: https://github.com/kezabelle/django-adminlinks/issues/
.. _my Twitter account: https://twitter.com/kezabelle/
