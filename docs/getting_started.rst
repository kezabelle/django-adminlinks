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
* `Django`_ >= 1.2,<1.5

.. _django-classy-tags: http://django-classy-tags.readthedocs.org/
.. _0.3.4.1: http://pypi.python.org/pypi/django-classy-tags/0.3.4.1
.. _Django: https://docs.djangoproject.com/


Installation
------------

Because I don't believe in polluting the `PyPI`_ with half-finished or
abandonware installables, the only way to install django-adminlinks at this
time is either via cloning the Git repository directly into your pythonpath, or
having `pip`_ do it for you::
 
    pip install git+https://github.com/kezabelle/django-adminlinks.git

Once the package is installed, you'll need to update your `Django`_ project
settings (usually ``settings.py``) and add ``adminlinks`` to your
``INSTALLED_APPS``::

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
have `loaded the correct template tags`_. Mostly, that means::

    {% load adminlinks_buttons %}

With the buttons loaded for the template, you can sprinkle whatever links you
want for a given ``object``, like so::

    <div class="headline">{{ object.title }}</div>
    
    <!-- Your basic actions -->
    {% render_edit_button object %}
    {% render_delete_button object %}

    <!-- Are there other tags available? Why yes, there are! -->
    {% render_add_button object %} 
    {% render_history_button object %}
    {% render_edit_fields_button object 'title' 'description' %}

    <!-- there's also a grouped button, which handles add/edit/delete/history --> 
    {% render_admin_buttons object %}

.. warning::
    At this point, those template tags won't output anything, regardless of your
    permissions. There's no reason to panic, but we've not been through
    :ref:`enable_modeladmin` yet.

.. _loaded the correct template tags: https://docs.djangoproject.com/en/dev/ref/templates/builtins/#load

.. _enable_modeladmin:

Enabling Modeladmins
--------------------

By default, to preserve whatever existing functionality your project has, you
can pepper your templates with the new template tags, and nothing will be
displayed, to you, or anyone else; regardless of permissions, staff or
superuser status.

To allow for linking from these template tags to the `AdminSite`, every
modeladmin you want access needs to be modified to provide a new method,
``has_frontend_permission``, which needs to return ``True`` or ``False``. At
it's most naïve, this would be the simplest implementation::

    def has_frontend_permission(self, request, obj=None):
        return True

Which would do the job of *registering* the modeladmin as available for the
template tags to use. The exercise of tailoring ``has_frontend_permission`` to
perform a more complex role is left to the reader. It has the same signiture of
``has_change_permission`` *et al* for that reason.

Keeping some modeladmins hidden is easy: Any which lack the method
``has_frontend_permission`` (which is all of them, if you've just started out
with django-adminlinks) will never even get considered for display.

A few niceities 
---------------

When all's said and done, bouncing back and forth between the `AdminSite` and
the frontend isn't the nicest experience, though it's made somewhat easier by
having buttons sprinkled everywhere; In non-complex scenarios,
django-adminlinks goes that far, and a little further, providing a few
:doc:`Optional, replaceable extras <extras>`.

