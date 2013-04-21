# -*- coding: utf-8 -*-
from __future__ import unicode_literals

#: The format for getting any admin url, in any single-level URL namespace.
MODELADMIN_REVERSE = '%(namespace)s:%(app)s_%(module)s_%(view)s'

#: Generic string format for getting methods on a
#: :class:`~django.contrib.admin.ModelAdmin` which define permissions
#:
#: .. seealso:: :func:`~adminlinks.templatetags.utils.get_registered_modeladmins`
PERMISSION_ATTRIBUTE = 'has_%s_permission'

#: a semi-secret attribute set onto
#: :func:`~adminlinks.templatetags.utils.get_admin_site` to stash away all
#: discovered valid :class:`~django.contrib.admin.sites.AdminSite` instances.
GET_ADMIN_SITES_KEY = '_found_previously'


#: Used through-out the :class:`~adminlinks.admin.AdminlinksMixin` to test
#: whether or not we're in a popup window.
POPUP_QS_VAR = '_popup'

#: Used through-out the :class:`~adminlinks.admin.AdminlinksMixin` to test
#: whether or not we're in a popup window, and frontend editing.
FRONTEND_QS_VAR = '_frontend_editing'
