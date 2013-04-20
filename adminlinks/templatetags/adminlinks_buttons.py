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


class BaseAdminLink(object):
    """
    Class for mixing into other classes to provide
    :meth:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.is_valid`,
    allowing subclasses to test the incoming data and react accordingly::

    class MyContextHandler(BaseAdminLink):
        def get_context(self, context, obj):
            assert self.is_valid(context, obj) == True

    Also provides
    :attr:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.base_options`
    suitable for using in classy tags.
    """

    #: Default options involved in :class:`~classytags.helpers.InclusionTag`
    #: subclasses. Stored as a tuple because manipulating Options lists is
    #: more difficult than we'd like;
    #: see https://github.com/ojii/django-classy-tags/issues/14
    base_options = (Argument('obj', required=True),
                    StringArgument('admin_site', required=False, default='admin'),
                    Argument('querystring', required=False, default='_popup=1'))

    def is_valid(self, context, obj, *args, **kwargs):
        """
        Performs some basic tests against the parameters passed to it to
        ensure that work should carry on afterwards.

        :param context: a :class:`~django.template.context.BaseContext` subclass,
                        or dictionary-like object which fulfils certain criteria.
                        Usually a :class:`~django.template.context.RequestContext`.
        :param obj: the :class:`~django.db.models.Model`, either as a class or
                    an instance. Or, more specifically, anything which as a
                    :class:`~django.db.models.options.Options` object stored
                    under the `_meta` attribute.

        :return: whether or not the context and object pair are valid.
        :rtype: :data:`True` or :data:`False`

        .. seealso:: :func:`~adminlinks.templatetags.utils.context_passes_test`
        """

        if not hasattr(obj, '_meta'):
            logger.debug('Object has no _meta attribute')
            return False

        # This is to support editregions, which in turn depends on adminlinks.
        # Yay for circular dependencies at a package level.
        if fake_context_payload in context:
            logger.debug('Fake payload discovered in context')
            return False

        if not context_passes_test(context):
            logger.debug('Invalid context')
            return False

        return True

class Edit(BaseAdminLink, InclusionTag):
    template = 'adminlinks/edit_link.html'

    options = Options(*BaseAdminLink.base_options)

    def get_context(self, context, obj, admin_site, querystring):
        if not self.is_valid(context, obj):
            return context

        context.update(_add_link_to_context(admin_site, context['request'],
                                            obj._meta, 'change', [obj.pk],
                                            query=querystring))
        return context
register.tag(name='render_edit_button', compile_function=Edit)


class EditField(BaseAdminLink, InclusionTag):
    template = 'adminlinks/edit_field_link.html'

    options = Options(BaseAdminLink.base_options[0],  # obj
                      StringArgument('fieldname', required=True),
                      *BaseAdminLink.base_options[1:])  # admin_site, querystring

    def get_context(self, context, obj, fieldname, admin_site, querystring):
        if not self.is_valid(context, obj):
            return context

        context.update(_add_custom_link_to_context(admin_site, context['request'],
                                                   obj._meta, 'change',
                                                   'change_field',
                                                   [obj.pk, fieldname],
                                                   query=querystring))
        # successfully loaded link, add the fieldname.
        if 'link' in context:
            context.update({'verbose_name': obj._meta.get_field_by_name(fieldname)[0].verbose_name})
        return context
register.tag(name='render_edit_field_button', compile_function=EditField)


class Delete(BaseAdminLink, InclusionTag):
    template = 'adminlinks/delete_link.html'

    options = Options(*BaseAdminLink.base_options)

    def get_context(self, context, obj, admin_site, querystring):
        if not self.is_valid(context, obj):
            return context

        context.update(_add_link_to_context(admin_site, context['request'],
                                            obj._meta, 'delete', [obj.pk],
                                            query=querystring))
        return context
register.tag(name='render_delete_button', compile_function=Delete)


class Add(BaseAdminLink, InclusionTag):
    template = 'adminlinks/add_link.html'

    options = Options(*BaseAdminLink.base_options)

    def get_context(self, context, obj, admin_site, querystring):
        if not self.is_valid(context, obj):
            return context

        context.update(_add_link_to_context(admin_site, context['request'],
                                            obj._meta, 'add', None,
                                            query=querystring))
        return context
register.tag(name='render_add_button', compile_function=Add)


class History(BaseAdminLink, InclusionTag):
    template = 'adminlinks/history_link.html'

    options = Options(*BaseAdminLink.base_options)

    def get_context(self, context, obj, admin_site, querystring):
        context.update(_add_link_to_context(admin_site, context['request'],
                                            obj._meta , 'history', [obj.pk],
                                            query=querystring))
        return context
register.tag(name='render_history_button', compile_function=History)


class ChangeList(BaseAdminLink, InclusionTag):
    template = 'adminlinks/changelist_link.html'

    #: This needs to have a different default querystring, because of
    #: https://code.djangoproject.com/ticket/20288#ticket
    options = Options(BaseAdminLink.base_options[0],  # obj
                      BaseAdminLink.base_options[1],  # admin_site
                      Argument('querystring', required=False, default='pop=1'))

    def get_context(self, context, obj, admin_site, querystring):
        if not self.is_valid(context, obj):
            return context

        context.update(_add_link_to_context(admin_site, context['request'],
                                            obj._meta , 'changelist', None,
                                            query=querystring))
        return context
register.tag(name='render_changelist_button', compile_function=ChangeList)


class Combined(BaseAdminLink, InclusionTag):
    template = 'adminlinks/grouped_link.html'

    # TODO: support querystrings here.
    options = Options(
        Argument('obj', required=True),
        StringArgument('admin_site', required=False, default='admin'),
    )

    def get_context(self, context, obj, admin_site):
        if not self.is_valid(context, obj):
            return context

        opts = obj._meta
        site = get_admin_site(admin_site)
        if site is None:
            logger.debug('Invalid admin site')
            return context

        admins = get_registered_modeladmins(context['request'], site)
        lookup = (opts.app_label.lower(), opts.module_name.lower())

        if not lookup in admins:
            logger.debug('%s:%s not in admin' % lookup)
            return context

        modeladmin_links = admins[lookup]
        links = {
            'add': _admin_link_shortcut(
                modeladmin_links.get('add', '')
            ),
            'change': _admin_link_shortcut(
                modeladmin_links.get('change', ''), [obj.pk]
            ),
            'history': _admin_link_shortcut(
                modeladmin_links.get('history', ''), [obj.pk]
            ),
            'delete': _admin_link_shortcut(
                modeladmin_links.get('delete', ''), [obj.pk]
            ),
        }
        context.update({'links': links, 'verbose_name': opts.verbose_name})
        return context
register.tag(name='render_admin_buttons', compile_function=Combined)
