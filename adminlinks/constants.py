# -*- coding: utf-8 -*-
from __future__ import unicode_literals

#: The format for getting any admin url, in any single-level URL namespace.
#:
#: .. seealso:: :func:`~adminlinks.templatetags.utils.get_registered_modeladmins`
#: .. seealso:: :func:`~adminlinks.templatetags.utils._add_custom_link_to_context`
MODELADMIN_REVERSE = '%(namespace)s:%(app)s_%(module)s_%(view)s'

#: Generic string format for getting methods on a
#: :class:`~django.contrib.admin.ModelAdmin` which define permissions
#:
#: .. seealso:: :func:`~adminlinks.templatetags.utils.get_registered_modeladmins`
PERMISSION_ATTRIBUTE = 'has_%s_permission'

#: a semi-secret attribute set onto our function to stash away all
#: discovered valid :class:`~django.contrib.admin.sites.AdminSite` instances.
#:
#: .. seealso:: :func:`~adminlinks.templatetags.utils.get_admin_site`
GET_ADMIN_SITES_KEY = '_found_previously'
