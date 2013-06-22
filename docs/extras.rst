.. links go here
.. _Twitter Bootstrap: http://twitter.github.com/bootstrap/
.. _django-sekizai: http://django-sekizai.readthedocs.org/
.. _django-compressor: http://django_compressor.readthedocs.org/
.. _jQuery: http://jquery.com/
.. _jQuery ajaxForm: http://www.malsup.com/jquery/form/

Optional, replaceable extras
============================

In the :doc:`installation and basic usage <getting_started>` we covered the
bare minimum required to display plain text links to the admin. We can, of
course, do better than that, and django-adminlinks comes with a few bits and
pieces to do so. None of them are required, or even enabled by default, and all
of them are replaceable.


Styling the links
-----------------

If you're lucky, they'll already look as nice as your regular links, because
that's all they are. Don't believe me? Here's the default template for the edit
link:

.. literalinclude:: ../adminlinks/templates/adminlinks/edit_link.html
    :language: django

As you can see, the links can be styled in a composite way because they have
multiple classes.

.. _bundled_css:

Using the provided styles
^^^^^^^^^^^^^^^^^^^^^^^^^

There's a template tag we've not mentioned until now, because it's not suitable
for use with things like `django-sekizai`_ or `django-compressor`_.

Behold ``render_adminlinks_css``::

    {% load adminlinks_assets %}
    <!doctype html>
    <html>
        <head>
            {% render_adminlinks_css %}
        </head>
        <body>
            [...]
        </body>
    </html>

That's all there is to it. Infact, it's not even a complex tag, it just handles
rendering this on your behalf and does so if the ``request.user`` can
potentially use the `AdminSite`:

.. literalinclude:: ../adminlinks/templates/adminlinks/css.html
    :language: django

The styles in ``widgets.css`` are designed to emulate the visuals of the
default Django admin, without using any images. You can override them by
providing your own ``widgets.css``, or override the
``adminlinks/templates/adminlinks/css.html`` file in your own templates,
wherever you've specified them under ``TEMPLATE_DIRS``.

.. note::
    If you're using either `django-sekizai`_ or `django-compressor`_,
    you'll need to handle whether or not the stylesheets should be displayed
    yourself. Or you can just always include them, I suppose.

As you can see, the ``{% render_adminlinks_css %}`` also renders another
stylesheet, ``fancyiframe-custom.css``, which is used in conjunction with the
provided javascript.

Making things modal
-------------------

Though it is inevitably not perfect, we can make the UX a little better by
allowing users to edit things *in-place*, via the included modal iframe.

.. _bundled_js:

Using the provided JavaScript
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Exactly like the  :ref:`bundled Stylesheets template tag <bundled_css>`,
there's a template tag for rendering the bundled JavaScript. The same caveats
about `django-sekizai`_ and `django-compressor`_ apply::

    {% load adminlinks_assets %}
    <!doctype html>
    <html>
        <head>
            [...]
        </head>
        <body>
        [...]
            {% render_adminlinks_js %}
        </body>
    </html>

Which will output:

.. literalinclude:: ../adminlinks/templates/adminlinks/js.html

As you can see, the JavaScript is a little bit more involved. It uses the
`jQuery`_ which comes with Django, and a script of my own wrangling, to display
an ``<iframe>`` in a modal box. It hooks up all classes of ``admin-add``,
``admin-edit``, ``admin-delete``, and ``admin-history`` to this modal box, and
modifies the target URL (the modeladmin view)

Patching the standard ModelAdmin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you're making use of the :ref:`bundled JavaScript <bundled_js>`, through the
template tag or otherwise, you'll probably want to alter the behaviour of the
Django ModelAdmin instances in an effort to better support the modal-editing

Flash Messages
""""""""""""""

To hide the flash messages Django levis on successful modeladmin actions,
so that opening a new popup doesn't show an old message, there is a simple
:class:`~adminlinks.admin.HideMessages`.

Editing field subsets
"""""""""""""""""""""

If your intention is to use the **edit fields** template tag::

    {% render_edit_fields_button object 'title' 'description' %}

You'll need to amend the modeladmin to support the dynamic generation of that
form, using the :class:`~adminlinks.admin.ChangeFieldView`, which updates the
standard urls to expose the :meth:`~adminlinks.admin.ChangeFieldView.change_field_view`

Success responses
"""""""""""""""""

Unfortunately, this means overriding or patching the existing modeladmin
methods :meth:`~django.contrib.admin.options.ModelAdmin.response_add` and
:meth:`~django.contrib.admin.options.ModelAdmin.response_change` to handle our
new request type. We provide the :class:`~adminlinks.admin.SuccessResponses`
for this purpose, though it may clobber existing responses.

Mashing them all together
"""""""""""""""""""""""""

As a courtesy, to opt-in to all of the above mixin classes,
a Mixin object, :class:`~adminlinks.admin.AdminlinksMixin` is provided. We can
use it like so:

.. literalinclude:: _admin_mixin.py
    :language: python
    :lines: 1-8

Or, for the slightly more complex usage of replacing a third-party admin:

.. literalinclude:: _admin_mixin.py
    :language: python
    :lines: 12-26

For more complex admins, or different ways of handling displaying things (such
as using `jQuery ajaxForm`_, or one of the many other modal boxes) you'll have
to go off the beaten track and drop some/most of the provided stuff. Any
suggestions for how to make it more flexible, do :ref:`get in contact
<contributing>` and explain.

