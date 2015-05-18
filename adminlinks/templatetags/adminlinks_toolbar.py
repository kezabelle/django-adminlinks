# -*- coding: utf-8 -*-
from classytags.arguments import StringArgument
from classytags.core import Options
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template.base import Library
from adminlinks.utils import _get_template_context
from classytags.helpers import InclusionTag

register = Library()


class AdminlinksToolbar(InclusionTag):
    template = 'adminlinks/toolbar.html'

    options = Options(
        StringArgument('admin_site', required=False, default='admin'),
    )

    def get_context(self, context, admin_site):
        if 'request' not in context:
            if settings.DEBUG:
                raise ImproperlyConfigured(
                    "To continue using this, you need to put "
                    "`django.core.context_processors.request` in your "
                    "TEMPLATE_CONTEXT_PROCESSORS, or pass `request` from your "
                    "view context to the template.")
        request = context['request']
        context['adminlinks'] = _get_template_context(request=request,
                                                      admin_site=admin_site)
        return context
register.tag(name='adminlinks_toolbar', compile_function=AdminlinksToolbar)
