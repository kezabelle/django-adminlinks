# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from classytags.arguments import Argument, StringArgument
from classytags.core import Options
from django.template.base import Library
from classytags.helpers import InclusionTag
from adminlinks.templatetags.utils import (context_passes_test,
                                           get_admin_site,
                                           get_registered_modeladmins,
                                           _admin_link_shortcut,
                                           _add_link_to_context,
                                           _add_custom_link_to_context)

try:
    from editregions.utils.regions import fake_context_payload
except ImportError:
    fake_context_payload = 'nothing_should_ever_match_this'

register = Library()
logger = logging.getLogger(__name__)







class AdminlinksEdit(InclusionTag):
    name = 'render_edit_button'
    template = 'adminlinks/edit_link.html'

    options = Options(
        Argument(u'obj', required=True),
        StringArgument(u'admin_site', required=False, default='admin'),
        Argument(u'querystring', required=False, default='')
    )

    def get_context(self, context, obj, admin_site, querystring):
        if not hasattr(obj, '_meta') or fake_context_payload in context:
            return context

        if context_passes_test(context):
            context.update(_add_link_to_context(admin_site, context['request'], obj._meta,
                'change', [obj.pk]))
        return context
register.tag(AdminlinksEdit)


class AdminlinksEditField(InclusionTag):
    name = 'render_edit_field_button'
    template = 'adminlinks/edit_field_link.html'

    options = Options(
        Argument(u'obj', required=True),
        Argument(u'fieldname', required=True),
        StringArgument(u'admin_site', required=False, default='admin'),
    )

    def get_context(self, context, obj, fieldname, admin_site):
        if not hasattr(obj, '_meta'):
            logger.debug('Object has no _meta attribute')
            return context

        if fake_context_payload in context:
            logger.debug('Fake payload discovered in context')
            return context

        if not context_passes_test(context):
            logger.debug('Invalid context')
            return context

        context.update(_add_custom_link_to_context(admin_site, context['request'], obj._meta,
            'change', 'change_field', [obj.pk, fieldname]))
        # successfully loaded link, add the fieldname.
        if u'link' in context:
            context.update({u'verbose_name': obj._meta.get_field_by_name(fieldname)[0].verbose_name})
        return context
register.tag(AdminlinksEditField)


class AdminlinksDelete(InclusionTag):
    name = 'render_delete_button'
    template = 'adminlinks/delete_link.html'

    options = Options(
        Argument(u'obj', required=True),
        StringArgument(u'admin_site', required=False, default='admin'),
    )

    def get_context(self, context, obj, admin_site):
        if not hasattr(obj, '_meta') or fake_context_payload in context:
            return context

        if context_passes_test(context):
            context.update(_add_link_to_context(admin_site, context['request'], obj._meta,
                'delete', [obj.pk]))
        return context
register.tag(AdminlinksDelete)


class AdminlinksAdd(InclusionTag):
    name = 'render_add_button'
    template = 'adminlinks/add_link.html'

    options = Options(
        Argument(u'obj', required=True),
        StringArgument(u'admin_site', required=False, default='admin'),
    )

    def get_context(self, context, obj, admin_site):
        if not hasattr(obj, '_meta') or fake_context_payload in context:
            return context

        if context_passes_test(context):
            context.update(_add_link_to_context(admin_site, context['request'], obj._meta,
                'add', None))
        return context
register.tag(AdminlinksAdd)


class AdminlinksHistory(InclusionTag):
    name = 'render_history_button'
    template = 'adminlinks/history_link.html'

    options = Options(
        Argument(u'obj', required=True),
        StringArgument(u'admin_site', required=False, default='admin'),
    )

    def get_context(self, context, obj, admin_site):
        if not hasattr(obj, '_meta') or fake_context_payload in context:
            return context

        if context_passes_test(context):
            context.update(_add_link_to_context(admin_site, context['request'], obj._meta ,
                'history', [obj.pk]))
        return context
register.tag(AdminlinksHistory)


class AdminlinksAll(InclusionTag):
    name = 'render_admin_buttons'
    template = 'adminlinks/grouped_link.html'

    options = Options(
        Argument(u'obj', required=True),
        StringArgument(u'admin_site', required=False, default='admin'),
    )

    def get_context(self, context, obj, admin_site):
        if not hasattr(obj, '_meta') or fake_context_payload in context:
            return context

        opts = obj._meta
        site = get_admin_site(admin_site)
        if site is None:
            return context

        admins = get_registered_modeladmins(context['request'], site)
        lookup = (opts.app_label.lower(), opts.module_name.lower())
        context_tests = [
            context_passes_test(context),
            lookup in admins.keys(),
        ]
        if all(context_tests):
            modeladmin_links = admins[lookup]
            links = {
                u'add': _admin_link_shortcut(
                    modeladmin_links.get(u'add', u'')
                ),
                u'change': _admin_link_shortcut(
                    modeladmin_links.get(u'change', u''), [obj.pk]
                ),
                u'history': _admin_link_shortcut(
                    modeladmin_links.get(u'history', u''), [obj.pk]
                ),
                u'delete': _admin_link_shortcut(
                    modeladmin_links.get(u'delete', u''), [obj.pk]
                ),
            }
            context.update({u'links': links, u'verbose_name': opts.verbose_name})
        return context
register.tag(AdminlinksAll)

