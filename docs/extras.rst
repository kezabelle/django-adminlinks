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
multiple classes. All of them are of the namespace ``admin-toolbar-btn``, which
is basically the same naming scheme as `Twitter Bootstrap`_ uses, but prefixed
with ``admin-toolbar-``, which should hopefully avoid collisions with any
existing styles.

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
            {% render_adminlinks_css %
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
modifies the target URL (the modeladmin view) to append two values to the
querystring:

    * ``_popup=1`` is used by the Django admin to hide certain layout elements,
      such as the usual header. Every time you've ever hit the **+** icon next
      to a dropdown box in the admin, you've been using this.  *
      ``_frontend_editing=1`` isn't used by Django, but can be by
      django-adminlinks. It is provided simply to distinguish the originating
      request type.

Handling admin responses
^^^^^^^^^^^^^^^^^^^^^^^^

If you're making use of the :ref:`bundled JavaScript <bundled_js>`, through the
template tag or otherwise, you'll need to do more than :ref:`enable the
modeladmins <enable_modeladmin>` to get everything working correctly. This is
because the admin automatically redirects to the ``ChangeList`` after
successfully adding, editing or deleting an object, which isn't what we want
within our modal box.

Unfortunately, that means overriding or patching the existing modeladmin
methods :meth:`~django.contrib.admin.options.ModelAdmin.response_add` and
:meth:`~django.contrib.admin.options.ModelAdmin.response_change` to handle our
new request type.

Here's how we might do that:

.. literalinclude:: ../adminlinks/admin.py
    :language: python
    :lines: 124-135

.. literalinclude:: ../adminlinks/admin.py 
    :language: python
    :lines: 111-122

But wait, that's not all! Django doesn't actually look for the ``_popup`` key
in the request for views which aren't add/change, so our nice delete and
history links will expose the full Django admin layout, headers and all. We'd
prefer it to be more uniform, so let's fix that:

.. literalinclude:: ../adminlinks/admin.py
    :language: python
    :lines: 142-162

Now we've fixed the delete view, so that the ``_popup`` key is provided to the
context, and successful deletes, which would usually return an HTTP status code
of ``302`` are instead routed to our success template, which can be customised
any way we like, at the model, app or default level.

We still need to fix the history view, but that's a bit simpler, as it's
essentially a read-only view, which needs that pesky ``_popup`` in it's
context:

.. literalinclude:: ../adminlinks/admin.py
    :language: python
    :lines: 165-172

Frankly, it's a bit messy, and we certainly don't want to be doing that for
every modeladmin we've enabled, just because we've opted for a nicer :abbr:`UX
(User Experience)`.

Using the admin mixin
^^^^^^^^^^^^^^^^^^^^^

So we won't, because django-adminlinks has put all of this gumpf together into
a Mixin object, ``AdminlinksMixin``, found in ``adminlinks/admin.py``. We can
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

