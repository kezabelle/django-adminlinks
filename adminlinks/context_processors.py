# -*- coding: utf-8 -*-
import logging
from django.contrib import admin
from django.core.urlresolvers import reverse, NoReverseMatch

logger = logging.getLogger(__name__)


def fix_admin_popups(request):
    """
    Should you desire it, you can force the entire admin to behave
    as if it were in a popup. This may be useful if you're exposing
    the entire thing as a frontend-edited site.

    It forces all of the admin to believe that the request included
    `_popup=1` (or `pop=1` for the changelist in `Django_` < 1.6)
    and thus hides the header, breadcrumbs etc.

    It also keeps track of whether or not it was really requested
    via a popup, by populating the context with ``is_really_popup``,
    and it also detects whether the view is supposed to respond by
    closing a modal window on success by putting ``will_autoclose``
    into the context.

    .. note::
        If there is no user, or the user is not authenticated, the
        context will never contain any of the documented keys.

        If the :class:`~django.contrib.admin.AdminSite` in use isn't
        the default ``django.contrib.admin.site``, it will also
        fail (being unable to reverse the default admin), which is
        hopefully fine, because you should probably handle things
        yourself, you magical person.

    :return: a bunch of values tracking the request state, if successfuly.
    :rtype: dictionary.
    """
    valid_value = {'is_popup': True, 'is_admin_view': True,
                   'is_really_popup': '_popup' in request.REQUEST or
                                      'pop' in request.GET,
                   'will_autoclose': '_autoclose' in request.REQUEST}
    invalid_value = {}
    if not hasattr(request, 'user'):
        logger.debug("No user on request, probably don't need to fix popups")
        return invalid_value

    if not request.user.is_authenticated():
        logger.debug("user is anonymous; no point trying to fix popups as "
                     "they're not signed in.")
        return invalid_value

    try:
        url_prefix = reverse('%s:index' % admin.site.name)
    except NoReverseMatch as e:
        logger.info('admin is not mounted')
        return invalid_value

    if not request.path.startswith(url_prefix):
        logger.debug("Request path {path} is not within the admin "
                     "mounted under {admin}".format(path=request.path,
                                                    admin=url_prefix))
        return invalid_value

    return valid_value
