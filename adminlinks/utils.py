# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from collections import OrderedDict
import logging
from django.contrib.auth.models import AnonymousUser
from django.db.models import Model
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
try:
    from django.apps import apps
except ImportError:  # < Django 1.7
    apps = None
from django.contrib.admin import AdminSite, site as DefaultAdminSite
from django.core.urlresolvers import reverse
from django.core.urlresolvers import resolve
from django.core.urlresolvers import NoReverseMatch
from django.core.urlresolvers import Resolver404
from django.utils.text import capfirst


logger = logging.getLogger(__name__)


def __get_app_verbose_name(app_label):
    if apps is not None:
        return apps.get_app_config(app_label).verbose_name
    else:
        return app_label.title()



def get_adminsite(name='admin'):
    """
    May raise:
        NoReverseMatch
        Resolver404
    """
    if DefaultAdminSite.name == name:
        logger.info('Default site found')
        return DefaultAdminSite
    try:
        for_resolving = reverse('{}:index'.format(name))
    except NoReverseMatch:
        logger.error("Couldn't find AdminSite named '{name!s}'".format(name=name),
                     exc_info=1)
        return None
    try:
        wrapped_view = resolve(for_resolving)
    except Resolver404:
        logger.error("Couldn't get AdminSite function from "
                     "'{url!s}'".format(url=for_resolving), exc_info=1)
        return None
    index = wrapped_view.func
    # Django 1.9+ uses the decorator to put the admin site instance on the func.
    if hasattr(index, 'admin_site'):
        return index.admin_site
    # unwrap the view, because all AdminSite urls get wrapped with a
    # decorator which goes through AdminSite.admin_view
    try:
        adminsite = next(x.cell_contents for x in wrapped_view.func.__closure__
                     if isinstance(x.cell_contents, AdminSite))
    except StopIteration:
        logger.error("Failed to unwrap the adminsite itself", exc_info=1)
        return None
    return adminsite


def get_modeladmins_from_adminsite(request, adminsite=None):
    if adminsite is None:
        adminsite = get_adminsite(name='admin')
    if hasattr(adminsite, 'each_context'):
        adminsite_context = adminsite.each_context(request=request)
        if 'available_apps' in adminsite_context:
            return adminsite_context['available_apps']
    app_dict = {}
    models = adminsite._registry
    for model, model_admin in models.items():
        has_module_perms = model_admin.has_module_permission(request)
        if not has_module_perms:
            continue

        perms = model_admin.get_model_perms(request)

        # Check whether user has any perm for this module.
        # If so, add the module to the model_list.
        if True not in perms.values():
            continue

        app_label = model._meta.app_label
        info = (app_label, model._meta.model_name)
        model_dict = {
            'name': capfirst(model._meta.verbose_name_plural),
            'object_name': model._meta.object_name,
            'perms': perms,
        }
        if perms.get('change'):
            try:
                model_dict['admin_url'] = reverse('admin:%s_%s_changelist' % info, current_app=adminsite.name)
            except NoReverseMatch:
                pass
        if perms.get('add'):
            try:
                model_dict['add_url'] = reverse('admin:%s_%s_add' % info, current_app=adminsite.name)
            except NoReverseMatch:
                pass

        if app_label in app_dict:
            app_dict[app_label]['models'].append(model_dict)
        else:
            app_dict[app_label] = {
                'name': __get_app_verbose_name(app_label),
                'app_label': app_label,
                'app_url': reverse(
                    'admin:app_list',
                    kwargs={'app_label': app_label},
                    current_app=adminsite.name,
                ),
                'has_module_perms': has_module_perms,
                'models': [model_dict],
            }

    # Sort the apps alphabetically.
    app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())
    # Sort the models alphabetically within each app.
    for app in app_list:
        app['models'].sort(key=lambda x: x['name'])
    return app_list


def _get_template_context(request, admin_site):
    try:
        admin_index = reverse('{}:index'.format(admin_site))
    except NoReverseMatch:
        admin_index = None
    try:
        admin_change_password = reverse('{}:password_change'.format(admin_site))
    except NoReverseMatch:
        admin_change_password = None
    try:
        admin_logout = reverse('{}:logout'.format(admin_site))
    except NoReverseMatch:
        admin_logout = None
    site = get_adminsite(admin_site)
    apps = None
    if site is not None:
        apps = get_modeladmins_from_adminsite(request=request, adminsite=site)
    return {'apps': apps,
            'user': getattr(request, 'user', AnonymousUser()),
            'index': admin_index,
            'change_password': admin_change_password,
            'logout': admin_logout,
            'namespace': admin_site}




def get_modeladmin_links(model, model_class, modeladmin, admin):
    """
    So yeah, we don't have a `request` because:
    a) this is called by a template filter, so there's no context to play off.
    b) it's intended that the resulting JSON blob can be left on the site if
       the page is compiled to a static file, and use the dynamic JS to
       continue editing the backend; for something akin to django-medusa.

    """
    links = OrderedDict()
    namespace = admin.name
    url_root = '{}:{}_{}'.format(namespace, model._meta.app_label,
                                 model._meta.model_name)
    # got to ask isinstance because ModelClass.pk yields <property object ...>
    if hasattr(model, 'pk') and isinstance(model, Model):
        # ... this is verbose but the least magic/complex thing ...
        try:
            links['change'] = {
                'url': reverse('{}_change'.format(url_root), args=(model.pk,)),
                'title': _('Change %s') % force_text(model._meta.verbose_name),
            }
        except NoReverseMatch:
            logger.error("Couldn't resolve the change form for %(cls)r" % {
                'cls': model_class}, exc_info=1)
        try:
            links['history'] = {
                'url': reverse('{}_history'.format(url_root), args=(model.pk,)),
                'title': _('History'),
            }
        except NoReverseMatch:
            logger.error("Couldn't resolve the history page for %(cls)r" % {
                'cls': model_class}, exc_info=1)
        try:
            links['delete'] = {
                'url': reverse('{}_delete'.format(url_root), args=(model.pk,)),
                'title': _('Delete'),
            }
        except NoReverseMatch:
            logger.error("Couldn't resolve the delete confirm form for %(cls)r" % {  # noqa
                'cls': model_class}, exc_info=1)
    try:
        links['add'] = {
            'url': reverse('{}_add'.format(url_root)),
            'title': _('Add %s') % force_text(model._meta.verbose_name),
        }
    except NoReverseMatch:
            logger.error("Couldn't even resolve the add form for %(cls)r, "
                         "for shame!" % {
                'cls': model_class}, exc_info=1)
    return links
