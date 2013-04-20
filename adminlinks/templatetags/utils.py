# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import defaultdict
from urlparse import urlsplit, urlunsplit
from django.core.urlresolvers import reverse, resolve, NoReverseMatch
from adminlinks.constants import (GET_ADMIN_SITES_KEY,
                                  FRONTEND_EDITING_ADMIN_VAR, MODELADMIN_REVERSE,
                                  PERMISSION_ATTRIBUTE)
from django.http import QueryDict


def context_passes_test(context):
    """
    Given a context, determine whether a `user` exists, and if they see anything.

    :param context: a :class:`~django.template.context.RequestContext`. Accepts
                    any :class:`~django.template.context.Context` like object,
                    but it explicitly tests for a `request` key and `request.user`
    :return: whether or not the given context should allow further processing.
    :rtype: :type:`boolean`
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
    Given the name of an :class:`~django.contrib.admin.sites.AdminSite` instance,
    try to resolve that into an actual object, and store the result onto this
    function. Future calls to that same name will avoid finding the object all
    over again, opting for the cached copy.

    :param admin_site: the string name of an
                       :class:`~django.contrib.admin.sites.AdminSite` named
                       and mounted on the project.
    :return: an :class:`~django.contrib.admin.sites.AdminSite` instance matching
             that given in the `admin_site` parameter.
    :rtype: :class:`~django.contrib.admin.sites.AdminSite` or :data:`None`
    """

    # pop a dictionary onto this function and use it for keeping track
    # of discovered admin sites as they're found.
    known_sites = getattr(get_admin_site, GET_ADMIN_SITES_KEY, {})

    # Not previously used, so we'll do the more expensive lookup.
    if admin_site not in known_sites:
        try:
            for_resolving = reverse('%s:index' % admin_site)
            wrapped_view = resolve(for_resolving)
            # unwrap the view, because all AdminSite urls get wrapped with a
            # decorator which goes through
            # :meth:`~django.contrib.admin.sites.AdminSite.admin_view`
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
    classes attached to the given admin and compile a dictionary of Models
    visible to the current user, limiting the methods available
    (add/edit/history/delete) as appropriate.

    Always returns a dictionary, though it may be empty, and thus evaluate as Falsy.

    :param request: the current request, for permissions checking etc.
    :param admin_site: a concrete :class:`~django.contrib.admin.sites.AdminSite`
                       named and mounted on the project.
    :return: visible modeladmins.
    :rtype: :type:`dictionary`

    .. note:: for a :class:`~django.contrib.admin.options.ModelAdmin` to be
              considered and returned, it must have a `frontend_editing`
              attribute set to :data:`True`.
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


def _admin_link_shortcut(urlname, params=None, query=None):
    """
    Minor wrapper around :func:`~django.core.urlresolvers.reverse`, catching the
    :exc:`~django.core.urlresolvers.NoReverseMatch` that may be thrown, and
    instead returning an empty unicode string.

    :param urlname: the view, or named URL to be reversed
    :param params: any parameters (as `args`, not `kwargs`) required to create
                   the correct URL.
    :return: the URL discovered, or an empty string
    :rtype: unicode string
    """
    try:
        params = params or ()
        url = reverse(urlname, args=params)
    except NoReverseMatch:
        url = ''

    scheme, netloc, path, query2, frag = urlsplit(url, allow_fragments=False)
    existing_qs = QueryDict(query_string=query2, mutable=True)
    new_qs = QueryDict(query_string=query or '')
    existing_qs.update(new_qs)
    final_url = urlunsplit((scheme, netloc, path, existing_qs.urlencode(), frag))
    return final_url


def _add_link_to_context(admin_site, request, opts, permname, url_params,
                         query=None):
    """
    Find out if a model is in our known list (those with frontend editing enabled
    and at least 1 permission. If it's in there, try and reverse the URL to
    return a dictionary for the final Inclusion Tag's context.

    Always returns a dictionary with two keys, whose values may be empty strings.

    :param admin_site: the string name of an admin site; eg: `admin`
    :param request: the current `~django.core.handlers.wsgi.WSGIRequest`
    :param opts: the `_meta` Options object to get the `app_label` and
                `module_name` for the desired URL.
    :param permname: The permission name to find; eg: `add`, `change`, `delete`
    :param url_params: a list of items to be passed as `args` to the underlying
                       use of reverse.
    :param query: querystring to append.
    :return: a dictionary containing `link` and `verbose_name` keys, whose values
             are the reversed URL and the display name of the object. Both may
             be blank.
    :rtype: :type:`dictionary`
    """
    site = get_admin_site(admin_site)
    if site is not None:
        admins = get_registered_modeladmins(request, site)
        lookup = (opts.app_label.lower(), opts.module_name.lower())

        if lookup in admins.keys() and permname in admins[lookup]:
            link = _admin_link_shortcut(admins[lookup][permname], url_params, query)
            return {'link': link, 'verbose_name': opts.verbose_name}

    return {'link': '', 'verbose_name': ''}


def _add_custom_link_to_context(admin_site, request, opts, permname, viewname,
                                url_params, query=None):
    """
    Like `_add_link_to_context`, but allows for using a specific permission, and
    any named url on the modeladmin, with optional url parameters.

    Always returns a dictionary with two keys, whose values may be empty strings.

    :param admin_site: the string name of an admin site; eg: `admin`
    :param request: the current `~django.core.handlers.wsgi.WSGIRequest`
    :param opts: the `_meta` Options object to get the `app_label` and
                `module_name` for the desired URL.
    :param permname: The permission name to find; eg: `add`, `change`, `delete`
    :param viewname: The name of the view to find; eg: `changelist`, `donkey`
    :param url_params: a list of items to be passed as `args` to the underlying
                       use of reverse.
    :param query: querystring to append.
    :return: a dictionary containing `link` and `verbose_name` keys, whose values
             are the reversed URL and the display name of the object. Both may
             be blank.
    :rtype: :type:`dictionary`
    """
    site = get_admin_site(admin_site)
    if site is not None:
        admins = get_registered_modeladmins(request, site)
        lookup = (opts.app_label.lower(), opts.module_name.lower())

        if lookup in admins and permname in admins[lookup]:
            return {
                'link': _admin_link_shortcut(MODELADMIN_REVERSE % {
                    'namespace': site.name,
                    'app': lookup[0],
                    'module': lookup[1],
                    'view': viewname,
                }, params=url_params, query=query),
                'verbose_name': opts.verbose_name
            }
    return {'link': '', 'verbose_name': ''}


def _resort_modeladmins(modeladmins):
    unsorted_resultset = defaultdict(list)
    for keypair, datavalues in modeladmins.items():
        app, model = keypair
        unsorted_resultset[app].append(datavalues)

    resultset = list(unsorted_resultset.items())
    resultset.sort(key=lambda x: x[0])
    return resultset
