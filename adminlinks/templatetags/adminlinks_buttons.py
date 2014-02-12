# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from classytags.arguments import Argument, StringArgument, ChoiceArgument
from classytags.core import Options
from django.template.base import Library
from classytags.helpers import InclusionTag
from django.template.defaultfilters import yesno
from adminlinks.templatetags.utils import (context_passes_test,
                                           get_admin_site,
                                           get_registered_modeladmins,
                                           _admin_link_shortcut,
                                           _add_link_to_context,
                                           _add_custom_link_to_context)
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

    .. versionchanged:: 0.8.1
        The default template, ``adminlinks/edit_field_link.html`` now expects
        to be able to use ``{% load static %}`` if the field being edited is
        either a :class:`~django.db.models.BooleanField` or a
        :class:`~django.db.models.NullBooleanField`, so that it can render
        an icon.
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
        ctx = {}
        ctx.update(_add_custom_link_to_context(admin_site, context['request'],
                                               obj._meta, 'change',
                                               'change_field',
                                               [obj.pk, fieldname],
                                               query=querystring))
        # successfully loaded link, add the fieldname.
        if 'link' in ctx:
            field = obj._meta.get_field(fieldname)
            value = getattr(obj, fieldname, None)
            if field.get_internal_type() in ('BooleanField', 'NullBooleanField'):
                icon = 'admin/img/icon-%s.gif' % yesno(value, "yes,no,unknown")
                ctx.update(maybe_boolean=True, img=icon)
            ctx.update(verbose_name=field.verbose_name,
                       existing_value=value)
        return ctx
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
        ctx = _add_custom_link_to_context(admin_site, context['request'],
                                          opts=obj._meta, permname='change',
                                          viewname='changelist', url_params=None,
                                          query=querystring)
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
        app_key = opts.app_label
        if hasattr(opts, 'model_name'):
            model_key = opts.model_name
        else:
            model_key = opts.module_name
        lookup = (app_key.lower(), model_key.lower())

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
            'changelist': _admin_link_shortcut(
                modeladmin_links.get('changelist', '')
            ),
        }
        return {'links': links, 'verbose_name': opts.verbose_name,
                'verbose_name_plural': opts.verbose_name_plural}
register.tag(name='render_admin_buttons', compile_function=Combined)


class AdminRoot(InclusionTag):
    options = Options(BaseAdminLink.base_options[1],  # admin_site
                      BaseAdminLink.base_options[2],  # querystring
                      'for',
                      ChoiceArgument('who', required=False, resolve=False,
                                     default='staff', choices=['staff',
                                                               'superusers',
                                                               'anyone',
                                                               'all',
                                                               'no-one',
                                                               'noone',
                                                               'none']))
    template = 'adminlinks/admin_root_link.html'

    def get_context(self, context, *args, **kwargs):
        """
        Entry point for all subsequent tags. Tests the context and bails
        early if possible.
        """
        who_can_see = kwargs.get('who')
        if who_can_see in ('no-one', 'noone', 'none'):
            logger.debug("No-one should see; didn't check context")
            return {}
        if (who_can_see not in ('anyone', 'all')
                and not context_passes_test(context)):
            logger.debug('Invalid context; button visibility was restricted')
            return {}
        if who_can_see == 'staff' and not context['request'].user.is_staff:
            logger.debug('Valid context, but user is not marked as staff')
            return {}
        if (who_can_see == 'superusers'
                and not context['request'].user.is_superuser):
            logger.debug('Valid context, but user is not a superuser')
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


class AdminlinksToggle(AdminRoot):
    template = 'adminlinks/admin_toggle.html'
register.tag(name='render_toggle_button', compile_function=AdminlinksToggle)
