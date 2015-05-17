# -*- coding: utf-8 -*-
from classytags.arguments import StringArgument
from classytags.core import Options
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import NoReverseMatch
from django.core.urlresolvers import reverse
from django.template.base import Library
from adminlinks.utils import get_adminsite
from adminlinks.utils import get_modeladmins_from_adminsite
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
        site = get_adminsite(admin_site)
        if site is None:
            return context
        apps = get_modeladmins_from_adminsite(request=request, adminsite=site)
        try:
            admin_index = reverse('{}:index'.format(admin_site))
        except NoReverseMatch:
            admin_index = None
        context['adminlinks'] = {'apps': apps, 'admin_index': admin_index}
        return context
register.tag(name='adminlinks_toolbar', compile_function=AdminlinksToolbar)
register.tag(name='render_adminlinks_toolbar', compile_function=AdminlinksToolbar)
