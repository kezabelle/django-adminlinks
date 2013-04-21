All of the template tags
========================

Listed below are reference materials for all the template tags considered public
and suitable for use at this time. None are required.

Including shipped static assets
-------------------------------

May be used in a template by adding the following line before calling any of them::

    {% load adminlinks_assets %}

Or to put just some of the available tags in your template namespace you can do::

    {% load render_adminlinks_js from adminlinks_assets %}
    {% load render_adminlinks_css from adminlinks_assets %}

Asset tags
^^^^^^^^^^

.. automodule:: adminlinks.templatetags.adminlinks_assets
    :members:

Rendering links to an admin site
--------------------------------

May be used in a template by adding the following line before calling any of them::

    {% load adminlinks_buttons %}

Or to put just some of the available tags in your template namespace you can do::

    {% load render_edit_button from adminlinks_buttons %}
    {% load render_changelist_button from adminlinks_buttons %}

and so on.

Link tags
^^^^^^^^^

.. automodule:: adminlinks.templatetags.adminlinks_buttons
    :members:
