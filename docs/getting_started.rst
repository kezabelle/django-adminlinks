Getting started with django-adminlinks
======================================

For the purposes of this document, it is assumed that things like `pip`_ and
`virtualenv`_ are being used, as doing Django projects without them is almost
unthinkable.

.. _pip: http://www.pip-installer.org/
.. _virtualenv: http://www.virtualenv.org/


Prerequisite packages
---------------------

Beyond those recommendations above, django-adminlinks has the current
dependencies.

* `django-classy-tags`_ >= `0.3.4.1`_
* `Django`_ >= 1.4

.. _django-classy-tags: http://django-classy-tags.readthedocs.org/
.. _0.3.4.1: http://pypi.python.org/pypi/django-classy-tags/0.3.4.1
.. _Django: https://docs.djangoproject.com/

.. admonition:: The Django version requirement

    as far as I know, the only reason `Django`_ 1.2 & 1.3 don't work is
    because the built-in template tags for rendering the
    :ref:`CSS <bundled_css>` and :ref:`JS <bundled_js>` both make
    use of ``{% static %}``, where previously they'd have used
    ``{{ STATIC_URL }}`` or ``{{ MEDIA_URL }}``

Installation
------------

Because I don't believe in polluting the `PyPI`_ with half-finished or
abandonware installables, the only way to install django-adminlinks at this
time is either via cloning the Git repository directly into your pythonpath, or
having `pip`_ do it for you::

    pip install git+https://github.com/kezabelle/django-adminlinks.git@0.8.0

Once the package is installed, you'll need to update your `Django`_ project
settings (usually ``settings.py``) and add ``adminlinks`` to your
``INSTALLED_APPS``, so that the template tags are available::

    INSTALLED_APPS = (
        # These are all required.
        'django.contrib.auth',
        'django.contrib.admin',
        'django.contrib.contenttypes',
        [...]
        # our new app!
        'adminlinks',
        [...]
    )

.. _PyPI: http://pypi.python.org/

Basic Usage
-----------

Wherever you want to link to an object's admin from a template, you'll need to
have `loaded the correct template tags`_. Mostly, that means throwing the
following in at the top of the template you want to display links in::

    {% load adminlinks_buttons %}

With the buttons loaded for the template, you can sprinkle whatever links you
want for any valid object; in the following example, the context variable
`object` is a model instance::

    <div class="headline">{{ object.title }}</div>

    <!-- Your basic actions -->
    {% render_edit_button object %}
    {% render_delete_button object %}

    <!-- Are there other tags available? Why yes, there are! -->
    {% render_add_button object %}
    {% render_history_button object %}
    {% render_edit_field_button object 'title' %}

    <!-- there's also a grouped button, which handles add/edit/delete/history -->
    {% render_admin_buttons object %}

    <!-- there's a button for going to the admin index, too -->
    {% render_admin_button %}
    {% render_admin_button "my_custom_admin" %}

.. note::
    When we refer to a **valid object**, we generally mean a Django model
    or model instance.

.. _loaded the correct template tags: https://docs.djangoproject.com/en/dev/ref/templates/builtins/#load

