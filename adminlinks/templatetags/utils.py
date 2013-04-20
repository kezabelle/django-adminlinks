# -*- coding: utf-8 -*-
from collections import defaultdict
from django.core.urlresolvers import reverse, resolve, NoReverseMatch
from adminlinks.constants import (GET_ADMIN_SITES_KEY,
                                  FRONTEND_EDITING_ADMIN_VAR, MODELADMIN_REVERSE,
                                  PERMISSION_ATTRIBUTE)

def context_passes_test(context):
    """
    Given a context, determine whether a `user` exists, and if they see anything
    Returns a boolean.
    """
    if 'request' not in context:
        return False
    request = context['request']

    if not hasattr(request, 'user'):
        return False

    user = request.user
    valid_admin_conditions = [
        user.is_staff,
        user.is_active,
        len(user.get_all_permissions()) > 0,
    ]
    return all(valid_admin_conditions)

def get_admin_site(admin_site):
    """
    Given the name of an AdminSite instance, try to resolve that into an
    actual object, and store the result onto this function. Future calls
    to that same name will avoid finding the object all over again, opting
    for the cached copy.

    May return None, or an AdminSite.
    """

    # pop a dictionary onto this function and use it for keeping track
    # of discovered admin sites as they're found.
    known_sites = getattr(get_admin_site, GET_ADMIN_SITES_KEY, {})

    # Not previously used, so we'll do the more expensive lookup.
    if admin_site not in known_sites:
        try:
            for_resolving = reverse('%s:index' % admin_site)
            wrapped_view = resolve(for_resolving)
            admin_site_obj = wrapped_view.func.func_closure[0].cell_contents
            known_sites.update({
                unicode(admin_site_obj.name): admin_site_obj,
            })
            setattr(get_admin_site, GET_ADMIN_SITES_KEY, known_sites)
        except NoReverseMatch:
            return None

    return known_sites[admin_site]


def get_registered_modeladmins(request, admin_site):
    """
    Taken from django.contrib.admin.sites.AdminSite.index, find all ModelAdmin
    classes attached to the given admin_site (an already resolved AdminSite
    instance) and compile a dictionary of Models visible to the current user,
    limiting the methods available (add/edit/history/delete) as appropriate.

    Always returns a dictionary, though it may be empty, and thus evaluate as Falsy.
    """
    apps = defaultdict(dict)

    for model, model_admin in admin_site._registry.items():
        dict_key = (model._meta.app_label.lower(), model._meta.module_name.lower())

        user_and_modeladmin_tests = [
            request.user.has_module_perms(model._meta.app_label),
            getattr(model_admin, FRONTEND_EDITING_ADMIN_VAR, False),
        ]

        if all(user_and_modeladmin_tests):
            # TODO: if a model has parents, use get_parent_list on the Options
            # instance to test all base permissions.
            urlparts = {
                'namespace': admin_site.name,
                'app': model._meta.app_label,
                'module': model._meta.module_name,
                'view': 'history'
            }
            apps[dict_key].update({
                'name': model._meta.verbose_name,
                'history': MODELADMIN_REVERSE % urlparts,
            })
            for val in ('add', 'change', 'delete'):
                perm = getattr(model_admin, PERMISSION_ATTRIBUTE % val)
                urlparts.update({'view': val})
                if perm(request):
                    apps[dict_key].update({
                        val: MODELADMIN_REVERSE % urlparts,
                    })
    app_dict = dict(apps)
    return app_dict
