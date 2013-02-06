# -*- coding: utf-8 -*-
from django.template.base import Library
from classytags.helpers import InclusionTag
from adminlinks.templatetags.utils import context_passes_test

register = Library()


class AdminlinksCssShortcut(InclusionTag):
    template = 'adminlinks/css.html'

    def get_context(self, context):
        """
        Updates the *existing* context, putting a boolean onto it.

        Always returns the existing context.
        """
        result = context_passes_test(context)
        context.update({'should_load_assets': result})
        return context
register.tag(name='render_adminlinks_css', compile_function=AdminlinksCssShortcut)


class AdminlinksJsShortcut(InclusionTag):
    template = 'adminlinks/js.html'

    def get_context(self, context):
        """
        Updates the *existing* context, putting a boolean onto it.

        Always returns the existing context.
        """
        result = context_passes_test(context)
        context.update({'should_load_assets': result})
        return context
register.tag(name='render_adminlinks_js', compile_function=AdminlinksJsShortcut)

