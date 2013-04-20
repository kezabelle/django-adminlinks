# -*- coding: utf-8 -*-
from __future__ import unicode_literals

MODELADMIN_REVERSE = '%(namespace)s:%(app)s_%(module)s_%(view)s'
PERMISSION_ATTRIBUTE = 'has_%s_permission'
FRONTEND_EDITING_ADMIN_VAR = 'frontend_editing'
GET_ADMIN_SITES_KEY = '_found_previously'


# Note: _popup is hilariously hard coded throughout the admin.
POPUP_QS_VAR = '_popup'
FRONTEND_QS_VAR = '_frontend_editing'
