# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from classytags.arguments import Argument, StringArgument
from classytags.core import Options
from django.template.base import Library
from classytags.helpers import InclusionTag
from distutils.version import LooseVersion
from django import get_version
from adminlinks.templatetags.utils import (context_passes_test,
                                           get_admin_site,
                                           get_registered_modeladmins,
                                           _admin_link_shortcut,
                                           _add_link_to_context,
                                           _add_custom_link_to_context,
                                           convert_context_to_dict)
register = Library()
logger = logging.getLogger(__name__)


def _changelist_popup_qs():
    changelist_popup_qs = 'pop=1'
    if LooseVersion(get_version()) >= LooseVersion('1.6'):
        changelist_popup_qs = '_popup=1'
    return changelist_popup_qs


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
                    Argument('querystring', required=False, default=''))

    def is_valid(self, context, obj, *args, **kwargs):
        """
        Performs some basic tests against the parameters passed to it to
        ensure that work should carry on afterwards.

        :param context: a :class:`~django.template.Context` subclass,
                        or dictionary-like object which fulfils certain criteria.
                        Usually a :class:`~django.template.RequestContext`.
        :param obj: the :class:`~django.db.models.Model`, either as a class or
                    an instance. Or, more specifically, anything which as a
                    :class:`~django.db.models.Options` object stored
                    under the `_meta` attribute.

        :return: whether or not the context and object pair are valid.
        :rtype: :data:`True` or :data:`False`

        .. seealso:: :func:`~adminlinks.templatetags.utils.context_passes_test`
        """

        if not hasattr(obj, '_meta'):
            logger.debug('Object has no _meta attribute')
            return False

        if not context_passes_test(context):
            logger.debug('Invalid context')
            return False

        return True

    def get_link_context(self, context, obj, *args, **kwargs):
        raise NotImplementedError('Subclass should implement this')

    def get_context(self, context, obj, *args, **kwargs):
        """
        Entry point for all subsequent tags. Tests the context and bails
        early if possible.
        """
        if not self.is_valid(context, obj):
            return {}
        return self.get_link_context(context, obj, *args, **kwargs)


class Edit(BaseAdminLink, InclusionTag):
    """
    An :class:`~classytags.helpers.InclusionTag` to render a link
    to the admin change form for an object::

        {% render_edit_button my_obj %}
        {% render_edit_button my_obj "my_custom_admin" %}
        {% render_edit_button my_obj "my_custom_admin" "a=1&b=2&a=3" %}
    """
    template = 'adminlinks/edit_link.html'

    # uses :attr:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.base_options`
    options = Options(*BaseAdminLink.base_options)

    def get_link_context(self, context, obj, admin_site, querystring):
        """
        Adds a `link` and `verbose_name` to the context, if
        :meth:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.is_valid`

        :param context: Hopefully, a :class:`~django.template.RequestContext`
                        otherwise :meth:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.is_valid`
                        is unlikely to be :data:`True`
        :param obj: the :class:`~django.db.models.Model` instance to link to.
                    Must have a primary key, and
                    :class:`~django.db.models.Options` from which we can
                    retrieve a :attr:`~django.db.models.Field.verbose_name`
        :param admin_site: name of the admin site to use; defaults to **"admin"**
        :param querystring: a querystring to include in the link output.
                            Defaults to "_popup=1"
        :return: the link values.
        :rtype: dictionary.
        """
        return _add_link_to_context(admin_site, context['request'],
                                    obj._meta, 'change', [obj.pk],
                                    query=querystring)
register.tag(name='render_edit_button', compile_function=Edit)


class EditField(BaseAdminLink, InclusionTag):
    """
    An :class:`~classytags.helpers.InclusionTag` to render a link
    to a customised admin change form for an object, showing only the requested
    field::

        {% render_edit_field_button my_obj "field_name" %}
        {% render_edit_field_button my_obj "field_name" "my_custom_admin" %}
        {% render_edit_field_button my_obj "field_name" "my_custom_admin" "a=1&b=2&a=3" %}

    .. note:: Use of this class requires that the
              :class:`~django.contrib.admin.ModelAdmin` includes
              :class:`~adminlinks.admin.AdminlinksMixin` or otherwise creates a
              named url ending in `change_field`.
    """
    template = 'adminlinks/edit_field_link.html'

    options = Options(BaseAdminLink.base_options[0],  # obj
                      StringArgument('fieldname', required=True),
                      *BaseAdminLink.base_options[1:])  # admin_site, querystring

    def get_link_context(self, context, obj, fieldname, admin_site, querystring):
        """
        Adds a `link` and `verbose_name` to the context, if
        :meth:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.is_valid`

        :param context: Hopefully, a :class:`~django.template.RequestContext`
                        otherwise :meth:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.is_valid`
                        is unlikely to be :data:`True`
        :param obj: the :class:`~django.db.models.Model` instance to link to.
                    Must have a primary key, and
                    :class:`~django.db.models.Options` from which we can
                    retrieve a :attr:`~django.db.models.Field.verbose_name`
        :param fieldname: the specific model field to render a link for.
        :param admin_site: name of the admin site to use; defaults to **"admin"**
        :param querystring: a querystring to include in the link output.
                            Defaults to "_popup=1"
        :return: the link values.
        :rtype: dictionary.
        """
        context = {}
        context.update(_add_link_to_context(admin_site, context['request'],
                                            obj._meta, 'change',
                                            [obj.pk, fieldname],
                                            query=querystring))
        # successfully loaded link, add the fieldname.
        if 'link' in context:
            context.update({'verbose_name':
                            obj._meta.get_field_by_name(fieldname)[0].verbose_name})
        return context
register.tag(name='render_edit_field_button', compile_function=EditField)


class Delete(BaseAdminLink, InclusionTag):
    """
    An :class:`~classytags.helpers.InclusionTag` to render a link
    to the delete confirmation form for an object::

        {% render_delete_button my_obj %}
        {% render_delete_button my_obj "my_custom_admin" %}
        {% render_delete_button my_obj "my_custom_admin" "a=1&b=2&a=3" %}
    """
    template = 'adminlinks/delete_link.html'

    # uses :attr:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.base_options`
    options = Options(*BaseAdminLink.base_options)

    def get_link_context(self, context, obj, admin_site, querystring):
        """
        Adds a `link` and `verbose_name` to the context, if
        :meth:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.is_valid`

        :param context: Hopefully, a :class:`~django.template.RequestContext`
                        otherwise :meth:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.is_valid`
                        is unlikely to be :data:`True`
        :param obj: the :class:`~django.db.models.Model` instance to link to.
                    Must have a primary key, and
                    :class:`~django.db.models.Options` from which we can
                    retrieve a :attr:`~django.db.models.Field.verbose_name`
        :param admin_site: name of the admin site to use; defaults to **"admin"**
        :param querystring: a querystring to include in the link output.
                            Defaults to "_popup=1"
        :return: the link values.
        :rtype: dictionary.
        """
        return _add_link_to_context(admin_site, context['request'],
                                    obj._meta, 'delete', [obj.pk],
                                    query=querystring)
register.tag(name='render_delete_button', compile_function=Delete)


class Add(BaseAdminLink, InclusionTag):
    """
    An :class:`~classytags.helpers.InclusionTag` to render a link
    to the :meth:`~django.contrib.admin.ModelAdmin.add_view` for a
    :class:`~django.db.models.Model` mounted onto a
    :class:`~django.contrib.admin.ModelAdmin` on the
    :class:`~django.contrib.admin.AdminSite`::

        {% render_add_button my_class %}
        {% render_add_button my_class "my_custom_admin" %}
        {% render_add_button my_class "my_custom_admin" "a=1&b=2&a=3" %}
    """
    template = 'adminlinks/add_link.html'

    # uses :attr:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.base_options`
    options = Options(*BaseAdminLink.base_options)

    def get_link_context(self, context, obj, admin_site, querystring):
        """
        Adds a `link` and `verbose_name` to the context, if
        :meth:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.is_valid`

        :param context: Hopefully, a :class:`~django.template.RequestContext`
                        otherwise :meth:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.is_valid`
                        is unlikely to be :data:`True`
        :param obj: the :class:`~django.db.models.Model` class to link to.
                    Must have :class:`~django.db.models.Options`
                    from which we can retrieve a
                    :attr:`~django.db.models.Field.verbose_name`
        :param admin_site: name of the admin site to use; defaults to **"admin"**
        :param querystring: a querystring to include in the link output.
                            Defaults to "_popup=1"
        :return: the link values.
        :rtype: dictionary.
        """
        return _add_link_to_context(admin_site, context['request'],
                                    obj._meta, 'add', None, query=querystring)
register.tag(name='render_add_button', compile_function=Add)


class History(BaseAdminLink, InclusionTag):
    """
    An :class:`~classytags.helpers.InclusionTag` to render a link
    to the object's :meth:`~django.contrib.admin.ModelAdmin.history_view` in a
    :class:`~django.contrib.admin.ModelAdmin` instance::

        {% render_history_button my_obj %}
        {% render_history_button my_obj "my_custom_admin" %}
        {% render_history_button my_obj "my_custom_admin" "a=1&b=2&a=3" %}
    """

    #: what gets rendered by this tag.
    template = 'adminlinks/history_link.html'

    # uses :attr:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.base_options`
    options = Options(*BaseAdminLink.base_options)

    def get_link_context(self, context, obj, admin_site, querystring):
        """
        Adds a `link` and `verbose_name` to the context, if
        :meth:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.is_valid`

        :param context: Hopefully, a :class:`~django.template.RequestContext`
                        otherwise :meth:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.is_valid`
                        is unlikely to be :data:`True`
        :param obj: the :class:`~django.db.models.Model` instance to link to.
                    Must have a primary key, and
                    :class:`~django.db.models.Options` from which we can
                    retrieve a :attr:`~django.db.models.Field.verbose_name`
        :param admin_site: name of the admin site to use; defaults to **"admin"**
        :param querystring: a querystring to include in the link output.
                            Defaults to "_popup=1"
        :return: the link values.
        :rtype: dictionary.
        """
        return _add_link_to_context(admin_site, context['request'],
                                    obj._meta, 'history', [obj.pk],
                                    query=querystring)
register.tag(name='render_history_button', compile_function=History)


class ChangeList(BaseAdminLink, InclusionTag):
    """
    An :class:`~classytags.helpers.InclusionTag` to render a link
    to the :meth:`~django.contrib.admin.ModelAdmin.changelist_view` (paginated
    objects) for a :class:`~django.contrib.admin.ModelAdmin` instance::

        {% render_changelist_button my_class %}
        {% render_changelist_button my_class "my_custom_admin" %}
        {% render_changelist_button my_class "my_custom_admin" "a=1&b=2&a=3" %}
    """

    template = 'adminlinks/changelist_link.html'

    # This needs to have a different default querystring, because of
    # https://code.djangoproject.com/ticket/20288#ticket
    options = Options(BaseAdminLink.base_options[0],  # obj
                      BaseAdminLink.base_options[1],  # admin_site
                      Argument('querystring', required=False, default=''))

    def get_link_context(self, context, obj, admin_site, querystring):
        """
        Adds a `link` and `verbose_name` to the context, if
        :meth:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.is_valid`

        :param context: Hopefully, a :class:`~django.template.RequestContext`
                        otherwise :meth:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.is_valid`
                        is unlikely to be :data:`True`
        :param obj: the :class:`~django.db.models.Model` class to link to.
                    Must have :class:`~django.db.models.Options`
                    from which we can retrieve a
                    :attr:`~django.db.models.Field.verbose_name`
        :param admin_site: name of the admin site to use; defaults to **"admin"**
        :param querystring: a querystring to include in the link output.
                            Defaults to "pop=1" unless Django > 1.6, when it
                            changes to "_popup=1"
        :return: the link values.
        :rtype: dictionary.
        """
        ctx = _add_link_to_context(admin_site, context['request'],
                                   obj._meta, 'change', None, query=querystring)
        if ctx['link']:
            logger.debug('link created successfully, swapping out the '
                         '`verbose_name` available to the context')
            ctx['verbose_name'] = obj._meta.verbose_name_plural
        return ctx
register.tag(name='render_changelist_button', compile_function=ChangeList)


class Combined(BaseAdminLink, InclusionTag):
    """
    This needs reworking, I think.
    """
    template = 'adminlinks/grouped_link.html'

    options = Options(
        Argument('obj', required=True),
        StringArgument('admin_site', required=False, default='admin'),
    )

    def get_link_context(self, context, obj, admin_site):
        """
        Wraps all the other adminlink template tags into one.

        :param context: Hopefully, a :class:`~django.template.RequestContext`
                        otherwise :meth:`~adminlinks.templatetags.adminlinks_buttons.BaseAdminLink.is_valid`
                        is unlikely to be :data:`True`
        :param obj: the :class:`~django.db.models.Model` class to link to.
                    Must have :class:`~django.db.models.Options`
                    from which we can retrieve a
                    :attr:`~django.db.models.Field.verbose_name`
        :param admin_site: name of the admin site to use; defaults to **"admin"**
        :return: the link values.
        :rtype: dictionary.
        """
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
        print(modeladmin_links)
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
            'changelist': _admin_link_shortcut(
                modeladmin_links.get('changelist', '')
            ),
        }
        return {'links': links, 'verbose_name': opts.verbose_name,
                'verbose_name_plural': opts.verbose_name_plural}
register.tag(name='render_admin_buttons', compile_function=Combined)


class AdminRoot(InclusionTag):
    options = Options(*BaseAdminLink.base_options[1:])  # admin_site, querystring
    template = 'adminlinks/admin_root_link.html'

    def get_context(self, context, *args, **kwargs):
        """
        Entry point for all subsequent tags. Tests the context and bails
        early if possible.
        """
        if not context_passes_test(context):
            logger.debug('Invalid context')
            return {}
        return self.get_link_context(context, *args, **kwargs)

    def get_link_context(self, context, admin_site, querystring, *args, **kwargs):
        site = get_admin_site(admin_site)
        if site is None:
            logger.debug('Invalid admin site ...')
            return {}
        index_link = _admin_link_shortcut('%(namespace)s:index' % {
            'namespace': site.name,
        }, params=None, query=querystring)
        return {
            'link': index_link
        }
register.tag(name='render_admin_button', compile_function=AdminRoot)
