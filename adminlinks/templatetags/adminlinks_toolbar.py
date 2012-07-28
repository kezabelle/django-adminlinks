# -*- coding: utf-8 -*-
from collections import defaultdict
from classytags.arguments import Flag, StringArgument
from classytags.core import Options
from django.template.base import Library
from classytags.helpers import InclusionTag
from adminlinks.templatetags.utils import (context_passes_test, get_admin_site,
                                           get_registered_modeladmins)

register = Library()

def _resort_modeladmins_for_toolbar(modeladmins):
    unsorted_resultset = defaultdict(list)
    for keypair, datavalues in modeladmins.items():
        app, model = keypair
        unsorted_resultset[app].append(datavalues)

    resultset = list(unsorted_resultset.items())
    resultset.sort(key=lambda x: x[0])
    return resultset


class AdminlinksToolbar(InclusionTag):
    name = 'render_adminlinks_toolbar'
    template = 'adminlinks/toolbar.html'

    options = Options(
        Flag('with_labels',
            true_values=['1', 'true', 'yes', 'on'],
            false_values=['0', 'false', 'no', 'off'],
            case_sensitive=False, default=True),
        StringArgument('admin_site', required=False, default='admin'),
    )

    def get_context(self, context, with_labels, admin_site):
        site = get_admin_site(admin_site)

        if context_passes_test(context) and site is not None:
            modeladmins = get_registered_modeladmins(context['request'], site)
            context.update({
                'should_display_toolbar': True,
                'should_display_apps': with_labels,
                'app_list': _resort_modeladmins_for_toolbar(modeladmins),
            })
        return context
register.tag(AdminlinksToolbar)
