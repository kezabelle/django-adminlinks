# -*- coding: utf-8 -*-
import logging
from django.contrib import admin
from django.core.urlresolvers import reverse, NoReverseMatch

logger = logging.getLogger(__name__)


def fix_admin_popups(request):
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
