# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import defaultdict
import logging
from distutils.version import LooseVersion
from django.contrib.admin import AdminSite, site as PossibleAdminSite

try:
    from django.utils.six.moves import urllib_parse
    urlsplit = urllib_parse.urlsplit
    urlunsplit = urllib_parse.urlunsplit
except (ImportError, AttributeError) as e:  # Python 2, < Django 1.5
    from urlparse import urlsplit, urlunsplit
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse, resolve, NoReverseMatch
# from django.utils.functional import memoize
from django.http import QueryDict
from adminlinks.constants import MODELADMIN_REVERSE, PERMISSION_ATTRIBUTE

logger = logging.getLogger(__name__)
_admin_sites_cache = {}


def context_passes_test(context):
    """
    Given a context, determine whether a
    :class:`~django.contrib.auth.models.User` exists, and if they see anything.

    .. versionchanged:: 0.8.1
        if ``DEBUG`` is :data:`True`, then better error messages are displayed
        to the user, as a reminder of what settings need to be in place.
        Previously it was dependent on having a ``LOGGING`` configuration that
        would show the messages.

    :param context: a :class:`~django.template.RequestContext`. Accepts
                    any :class:`~django.template.Context` like object,
                    but it explicitly tests for a `request` key and
                    `request.user`
    :return: whether or not the given context should allow further processing.
    :rtype: :data:`True` or :data:`False`
    """
    if 'request' not in context:
        logger.debug('request not found in context')
        if settings.DEBUG:
            raise ImproperlyConfigured("To continue using this, you need to "
                                       "put `django.core.context_processors.request` "
                                       "in your TEMPLATE_CONTEXT_PROCESSORS")
        return False
    request = context['request']

    if not hasattr(request, 'user'):
        logger.debug('%r has no "user"')
        if settings.DEBUG:
            raise ImproperlyConfigured("To continue using this, you need to "
                                       "put `django.contrib.auth.middleware.AuthenticationMiddleware` "
                                       "in your MIDDLEWARE_CLASSES")
        return False

    user = request.user
    valid_admin_conditions = [
        user.is_authenticated(),
        user.is_staff,
        user.is_active,
        len(user.get_all_permissions()) > 0,
    ]
    logger.debug('Tested conditions: %r' % valid_admin_conditions)
    return all(valid_admin_conditions)


def get_admin_site(admin_site):
    """
    Given the name of an :class:`~django.contrib.admin.AdminSite` instance,
    try to resolve that into an actual object

    .. note::
        This function is exposed in the public API as
        :func:`~adminlinks.templatetags.utils.get_admin_site`, which uses
        memoization to cache discovered :class:`~django.contrib.admin.AdminSite`
        objects.

    :param admin_site: the string name of an
                       :class:`~django.contrib.admin.AdminSite` named
                       and mounted on the project.
    :return: an :class:`~django.contrib.admin.AdminSite` instance matching
             that given in the `admin_site` parameter.
    :rtype: :class:`~django.contrib.admin.AdminSite` or :data:`None`
    """

    # pop a dictionary onto this function and use it for keeping track
    # of discovered admin sites as they're found.
    logger.debug('admin site not previously discovered, so do the lookup')
    if PossibleAdminSite.name == admin_site:
        logger.info('Default site found')
        return PossibleAdminSite
    try:
        logger.debug('Custom admin site, not monkeypatched into contrib.admin')
        for_resolving = reverse('%s:index' % admin_site)
        wrapped_view = resolve(for_resolving)
        # unwrap the view, because all AdminSite urls get wrapped with a
        # decorator which goes through
        # :meth:`~django.contrib.admin.AdminSite.admin_view`
        adminsite = next(x.cell_contents for x in wrapped_view.func.__closure__
                         if isinstance(x.cell_contents, AdminSite))
        return adminsite
    except (NoReverseMatch, StopIteration) as e:
        logger.exception("Failed to find adminsite.")
        return None
# get_admin_site = memoize(_get_admin_site, _admin_sites_cache, num_args=1)
# get_admin_site.__doc__ = """
# The public API implementation of
# :func:`~adminlinks.templatetags.utils._get_admin_site`, wrapped to use
# memoization.
# """


def get_registered_modeladmins(request, admin_site):
    """
    Taken from :class:`~django.contrib.admin.AdminSite`, find all
    :class:`~django.contrib.admin.ModelAdmin`
    classes attached to the given admin and compile a dictionary of
    :class:`~django.db.models.Model` types
    visible to the current :class:`~django.contrib.auth.models.User`, limiting
    the methods available (add/edit/history/delete) as appropriate.

    Always returns a dictionary, though it may be empty, and thus evaluate as Falsy.

    :param request: the current request, for permissions checking etc.
    :param admin_site: a concrete :class:`~django.contrib.admin.AdminSite`
                       named and mounted on the project.
    :return: visible :class:`~django.contrib.admin.ModelAdmin` classes.
    :rtype: :data:`dictionary`
    """
    apps = defaultdict(dict)

    for model, model_admin in admin_site._registry.items():
        app_key = model._meta.app_label
        if hasattr(model._meta, 'model_name'):
            model_key = model._meta.model_name
        else:
            model_key = model._meta.module_name
        dict_key = (app_key.lower(), model_key.lower())

        if request.user.has_module_perms(app_key):
            # TODO: if a model has parents, use get_parent_list on the Options
            # instance to test all base permissions.
            urlparts = {
                'namespace': admin_site.name,
                'app': app_key,
                'module': model_key,
            }

            apps[dict_key].update(name=model._meta.verbose_name)

            for val in ('history', 'changelist'):
                urlparts.update(view=val)
                apps[dict_key].update({
                    val: MODELADMIN_REVERSE % urlparts,
                })
            # require their permissions to be checked.
            for val in ('add', 'change', 'delete'):
                perm = getattr(model_admin, PERMISSION_ATTRIBUTE % val)
                urlparts.update(view=val)
                if perm(request):
                    urlname = MODELADMIN_REVERSE % urlparts
                    apps[dict_key].update({
                        val: urlname,
                        '%s_link' % val: _admin_link_shortcut(urlname)
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
        return ''

    scheme, netloc, path, query2, frag = urlsplit(url, allow_fragments=False)
    existing_qs = QueryDict(query_string=query2, mutable=True)
    new_qs = QueryDict(query_string=query or '')
    existing_qs.update(new_qs)
    final_url = urlunsplit((scheme, netloc, path, existing_qs.urlencode(), frag))
    return final_url


def _add_link_to_context(admin_site, request, opts, permname, url_params,
                         query=None):
    """
    Find out if a model is in our known list and at has least 1 permission.
    If it's in there, try and reverse the URL to return a dictionary for the
    final Inclusion Tag's context.

    Always returns a dictionary with two keys, whose values may be empty strings.

    :param admin_site: the string name of an admin site; eg: `admin`
    :param request: the current :class:`~django.core.handlers.wsgi.WSGIRequest`
    :param opts: the `_meta` Options object to get the `app_label` and
                `module_name` for the desired URL.
    :param permname: The permission name to find; eg: `add`, `change`, `delete`
    :param url_params: a list of items to be passed as `args` to the underlying
                       use of reverse.
    :param query: querystring to append.
    :return: a dictionary containing `link` and `verbose_name` keys, whose values
             are the reversed URL and the display name of the object. Both may
             be blank.
    :rtype: :data:`dictionary`
    """
    site = get_admin_site(admin_site)
    if site is not None:
        admins = get_registered_modeladmins(request, site)
        app_lookup = opts.app_label
        if hasattr(opts, 'model_name'):
            model_lookup = opts.model_name
        else:
            model_lookup = opts.module_name
        lookup = (app_lookup.lower(), model_lookup.lower())

        if lookup in admins.keys() and permname in admins[lookup]:
            link = _admin_link_shortcut(admins[lookup][permname], url_params, query)
            return {'link': link, 'verbose_name': opts.verbose_name}

    return {'link': '', 'verbose_name': ''}


def _add_custom_link_to_context(admin_site, request, opts, permname, viewname,
                                url_params, query=None):
    """
    Like :func:`~adminlinks.templatetags.utils._add_link_to_context`, but allows
    for using a specific named permission, and  any named url on the modeladmin,
    with optional url parameters.

    Uses :func:`~adminlinks.templatetags.utils._add_link_to_context` internally
    once it has established the permissions are OK.

    Always returns a dictionary with two keys, whose values may be empty strings.

    :param admin_site: the string name of an admin site; eg: `admin`
    :param request: the current :class:`~django.core.handlers.wsgi.WSGIRequest`
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
    :rtype: :data:`dictionary`
    """
    site = get_admin_site(admin_site)
    if site is not None:
        admins = get_registered_modeladmins(request, site)
        app_lookup = opts.app_label
        if hasattr(opts, 'model_name'):
            model_lookup = opts.model_name
        else:
            model_lookup = opts.module_name
        lookup = (app_lookup.lower(), model_lookup.lower())

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
    """
    A pulled-up-and-out version of the sorting the standard Django
    :class:`~django.contrib.admin.AdminSite` does on the index view.

    :param modeladmins: dictionary of modeladmins
    :return: the same modeladmins, with their ordering changed.
    :rtype: :data:`list`
    """
    unsorted_resultset = defaultdict(list)
    for keypair, datavalues in modeladmins.items():
        app, model = keypair
        unsorted_resultset[app].append(datavalues)

    resultset = list(unsorted_resultset.items())
    resultset.sort(key=lambda x: x[0])
    return resultset


def convert_context_to_dict(context):
    out = {}
    for d in context.dicts:
        for key, value in d.items():
            out[key] = value
    return out


def _changelist_popup_qs():
    """
    If we're not at 1.6, the changelist uses "pop" in the querystring.

    .. versionchanged:: 0.8.1
        Returns a tuple of the querystring and a boolean of whether or not
    """
    is_over_16 = LooseVersion(get_version()) >= LooseVersion('1.6')
    changelist_popup_qs = 'pop=1'
    if not is_over_16:
        changelist_popup_qs = '_popup=1'
    return changelist_popup_qs, is_over_16
