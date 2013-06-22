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
    under_the_hood


API information (auto-generated)
--------------------------------

.. toctree::
    :maxdepth: 3

    api/templatetags
    api/admin
    api/utils
    api/constants

What it is
----------

A suite of template tags for rendering links to a Django
:class:`~django.contrib.admin.AdminSite` instance.

At it's most basic, given a :class:`~django.db.models.Model`, it will do the
appropriate checks to ensure that the currently signed in user can perform the
requested action via the admin.

Why
---

Because I wedge the Django admin into everything, whether it should fit or not.
Not so much because I love the admin, but because it provides a well-understood
CRUD application that can be bolted onto in a pinch.

Features
--------

Here's a brief run-down on what's in the box:

* Basic, sane permission checking:

    * Calling the template tags without a RequestContext should not expose any
      markup.
    * Users must be signed in, and pass the permission checking for
      the specific administration view.

* Bundled with a smattering of CSS and JavaScript to make things a bit better.
* Pretty reasonable documentation. Or at least that's the aim.
* An additional view on all instances which subclass our `ModelAdmin`, to edit
  a specific field on a model, which can be used for some fairly neat in-place
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
