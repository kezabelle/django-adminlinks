# -*- coding: utf-8 -*-
import logging
from django.core.urlresolvers import resolve

logger = logging.getLogger(__name__)


def fix_admin_popups(request):
    valid_value = {'is_popup': '_popup' in request.REQUEST or
                               'pop' in request.GET}
    invalid_value = {}
    if not hasattr(request, 'user'):
        logger.debug("No user on request, probably don't need to fix popups")
        return invalid_value

    if request.user.is_anonymous():
        logger.debug("user is anonymous; no point trying to fix popups as "
                     "they're not signed in.")
        return invalid_value

    if request.path.startswith(('/admin/', '/administration/', '/backend/')):
        logger.info("Common admin URL prefix detected, assuming it's "
                    "an AdminSite")
        return valid_value

    try:
        resolved_func = resolve(request.path)
        real_func = resolved_func.func.func_closure[0].cell_contents
    except (AttributeError, IndexError) as e:
        logger.info('Resolved function is not wrapped the way I think admin '
                    'views should be...')
        return invalid_value

    if hasattr(real_func, 'admin_site'):
        logger.debug("ModelAdmin instance assumed; adding `is_popup` to context")
        return valid_value

    if hasattr(real_func, 'i18n_javascript') and hasattr(real_func, '_registry'):
        logger.debug("AdminSite instance assumed; adding `is_popup` to context")
        return valid_value
    #: Everything failed, so lets avoid
    #: "other_dict must be a mapping (dictionary-like) object."
    return invalid_value
