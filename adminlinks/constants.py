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

#: querystring key for tracking changes which might not otherwise be broadcast
#: by a success template being rendered.
DATA_CHANGED = '_data_changed'

#: querystring key for figuring out if we want to close a popup.
AUTOCLOSING = '_autoclose'
