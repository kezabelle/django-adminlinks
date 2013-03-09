# -*- coding: utf-8 -*-
import logging
from classytags.arguments import Argument, StringArgument
from classytags.core import Options
from django.core.urlresolvers import reverse, NoReverseMatch
from django.template.base import Library
from classytags.helpers import InclusionTag
from adminlinks.templatetags.utils import (context_passes_test,
                                           get_admin_site,
                                           get_registered_modeladmins,
                                           modeladmin_reverse)
try:
    from editregions.utils.regions import fake_context_payload
except ImportError:
    fake_context_payload = 'nothing_should_ever_match_this'

register = Library()
logger = logging.getLevelName(__name__)

def _admin_link_shortcut(urlname, params=None):
    try:
        params = params or ()
        return reverse(urlname, args=params)
    except NoReverseMatch:
        return u''

def _add_link_to_context(admin_site, request, opts, permname, url_params):
    """
    Find out if a model is in our known list (those with frontend editing enabled
    and at least 1 permission. If it's in there, try and reverse the URL to
    return a dictionary for the final Inclusion Tag's context.

    Always returns a dictionary with two keys, whose values may be empty strings.
    """
    site = get_admin_site(admin_site)
    if site is not None:
        admins = get_registered_modeladmins(request, site)
        lookup = (opts.app_label.lower(), opts.module_name.lower())

        if lookup in admins.keys() and permname in admins[lookup]:
            link = _admin_link_shortcut(admins[lookup][permname], url_params)
            return {u'link': link, u'verbose_name': opts.verbose_name}

    return {u'link': u'', u'verbose_name': u''}

def _add_custom_link_to_context(admin_site, request, opts, permname, viewname, url_params):
    """
    Like `_add_link_to_context`, but allows for using a specific permission, and
    any named url on the modeladmin, with optional url parameters.

    Always returns a dictionary with two keys, whose values may be empty strings.
    """
    site = get_admin_site(admin_site)
    if site is not None:
        admins = get_registered_modeladmins(request, site)
        lookup = (opts.app_label.lower(), opts.module_name.lower())

        if lookup in admins.keys() and permname in admins[lookup]:
             return {
                u'link': _admin_link_shortcut(modeladmin_reverse % {
                    u'namespace': site.name,
                    u'app': lookup[0],
                    u'module': lookup[1],
                    u'view': viewname,
                }, params=url_params),
                u'verbose_name': opts.verbose_name
            }
    return {u'link': u'', u'verbose_name': u''}

def _redefine_querystring(uri_query):
       return uri_query


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

