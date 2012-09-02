# -*- coding: utf-8 -*-
from django.template.base import Library
from classytags.helpers import InclusionTag
from adminlinks.templatetags.utils import context_passes_test

register = Library()


class AdminlinksCssShortcut(InclusionTag):
    name = 'render_adminlinks_css'
    template = 'adminlinks/css.html'

    def get_context(self, context):
        """
        Updates the *existing* context, putting a boolean onto it.
        
        Always returns the existing context.
        """
        result = context_passes_test(context)
        context.update({'should_load_assets': result})
        return context
register.tag(AdminlinksCssShortcut)


class AdminlinksJsShortcut(InclusionTag):
    name = 'render_adminlinks_js'
    template = 'adminlinks/js.html'

    def get_context(self, context):
        """
        Updates the *existing* context, putting a boolean onto it.
        
        Always returns the existing context.
        """
        result = context_passes_test(context)
        context.update({'should_load_assets': result})
        return context
register.tag(AdminlinksJsShortcut)

