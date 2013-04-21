# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.template.base import Library
from classytags.helpers import InclusionTag
from adminlinks.templatetags.utils import context_passes_test

register = Library()


class AdminlinksCssShortcut(InclusionTag):
    """
    Helper for rendering any Stylesheets (CSS) we want to ship by default. Can
    include inline (inside a `<style>` tag) or external (via a `<link>` tag)
    styles.
    """
    template = 'adminlinks/css.html'

    def get_context(self, context):
        """
        Tests and updates the existing context.

        :param context: a :class:`~django.template.Context` which is
                        checked via
                        :meth:`~adminlinks.templatetags.utils.context_passes_test`,
                        and the result **always** put into the context.
        :return: the context, possibly modified with a new layer.
        :rtype: :class:`~django.template.RequestContext` or other context/
                dictionary-like object.
        """
        result = context_passes_test(context)
        context.update({'should_load_assets': result})
        return context
register.tag(name='render_adminlinks_css', compile_function=AdminlinksCssShortcut)


class AdminlinksJsShortcut(InclusionTag):
    """
    Helper for rendering any JavaScript we want to ship by default,
    inline or as external scripts::

    {% render_adminlinks_js %}

    """
    #: How to call this tag from a template.
    name = 'render_adminlinks_js'

    #: The template to use to render the JavaScripts. May be overridden by
    #: project-level templates.
    template = 'adminlinks/js.html'

    def get_context(self, context):
        """
        Tests and updates the existing context.

        :param context: a :class:`~django.template.Context` which is
                        checked via
                        :meth:`~adminlinks.templatetags.utils.context_passes_test`,
                        and the result **always** put into the context.
        :return: the context, possibly modified with a new layer.
        :rtype: :class:`~django.template.RequestContext` or other context/
                dictionary-like object.
        """
        result = context_passes_test(context)
        context.update({'should_load_assets': result})
        return context
register.tag(name=AdminlinksJsShortcut.name, compile_function=AdminlinksJsShortcut)
