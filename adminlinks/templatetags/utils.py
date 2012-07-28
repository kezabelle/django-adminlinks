# -*- coding: utf-8 -*-
from collections import defaultdict
from django.core.urlresolvers import reverse, resolve, NoReverseMatch

def context_passes_test(context):
    """Given a context, determine whether a `user` exists, and if they see anything """
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
    # if it's been passed a string, we'll try to handle that, because we're
    # quite crazy.
    known_sites_key = '_found_previously'
    known_sites = getattr(get_admin_site, known_sites_key, {})

    # Not previously used, so we'll do the more expensive lookup.
    if admin_site not in known_sites:
        try:
            for_resolving = reverse('%s:index' % admin_site)
            wrapped_view = resolve(for_resolving)
            admin_site_obj = wrapped_view.func.func_closure[0].cell_contents
            known_sites.update({
                unicode(admin_site_obj.name): admin_site_obj,
                })
            setattr(get_admin_site, known_sites_key, known_sites)
        except NoReverseMatch:
            return None

    return known_sites[admin_site]

modeladmin_reverse = '%(namespace)s:%(app)s_%(module)s_%(view)s'

def get_registered_modeladmins(request, admin_site):
    """ Taken almost verbatim from django.contrib.admin.sites.AdminSite.index """
    apps = defaultdict(dict)

    for model, model_admin in admin_site._registry.items():
        dict_key = (model._meta.app_label.lower(), model._meta.module_name.lower())

        user_and_modeladmin_tests = [
            request.user.has_module_perms(model._meta.app_label),
            getattr(model_admin, 'frontend_editing', False),
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
                'history': modeladmin_reverse % urlparts,
            })
            for val in ('add', 'change', 'delete'):
                perm = getattr(model_admin, 'has_%s_permission' % val)
                urlparts.update({'view': val})
                if perm(request):
                    apps[dict_key].update({
                        val: modeladmin_reverse % urlparts,
                    })
    app_dict = dict(apps)
    return app_dict
