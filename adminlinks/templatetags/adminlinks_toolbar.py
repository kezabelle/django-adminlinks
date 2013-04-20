# -*- coding: utf-8 -*-
from classytags.arguments import Flag, StringArgument
from classytags.core import Options
from django.template.base import Library
from classytags.helpers import InclusionTag
from adminlinks.templatetags.utils import (context_passes_test, get_admin_site,
                                           get_registered_modeladmins,
                                           _resort_modeladmins)

register = Library()


class AdminlinksToolbar(InclusionTag):
    template = 'adminlinks/toolbar.html'

    options = Options(
        Flag('with_labels',
            true_values=['1', 'true', 'yes', 'on'],
            false_values=['0', 'false', 'no', 'off'],
            case_sensitive=False, default=True),
        StringArgument('admin_site', required=False, default='admin'),
    )

    def get_context(self, context, with_labels, admin_site):
        """
        Updates the *existing* context by putting a list of applicable
        modeladmins into `app_list` assuming the argument `admin_site`
        resolved into an AdminSite instance.

        Always returns the existing context.
        """
        site = get_admin_site(admin_site)

        if context_passes_test(context) and site is not None:
            modeladmins = get_registered_modeladmins(context['request'], site)
            context.update({
                'should_display_toolbar': True,
                'should_display_apps': with_labels,
                'app_list': _resort_modeladmins(modeladmins),
            })
        return context
register.tag(name='render_adminlinks_toolbar', compile_function=AdminlinksToolbar)
