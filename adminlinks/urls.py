# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from django.conf.urls import url
from .views import toolbar

adminlinks_toolbar_url = url(r'^admin/adminlinks/(?P<admin_site>[-a-zA-Z0-9_]+)/toolbar.js$', toolbar,
                  name="adminlinks_toolbar")
