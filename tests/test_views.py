# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from adminlinks.views import toolbar
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
import pytest


def test_invalid_site(rf):
    request = rf.get('/')
    request.user = AnonymousUser()
    with pytest.raises(Http404):
        toolbar(request=request, admin_site='lolwut')


def test_missing_user_middleware(rf):
    request = rf.get('/')
    with pytest.raises(Http404):
        toolbar(request=request, admin_site='admin')


def test_invalid_form_data(rf):
    request = rf.get('/', data={
        'include_html': False,
        'include_css': False,
        'js_namespace': 'test',
    })
    request.user = AnonymousUser()
    with pytest.raises(Http404):
        toolbar(request=request, admin_site='admin')


def test_wants_toolbar_html(rf):
    request = rf.get('/', data={
        'include_html': True,
        'include_css': False,
    })
    request.user = AnonymousUser()
    toolbar(request=request, admin_site='admin')

def test_does_not_want_toolbar_html(rf):
    request = rf.get('/', data={
        'include_html': False,
        'include_css': True,
    })
    request.user = AnonymousUser()
    toolbar(request=request, admin_site='admin')


def test_templates_resolution(rf):
    request = rf.get('/', data={
        'include_html': True,
        'include_css': True,
        'js_namespace': 'django'
    })
    request.user = AnonymousUser()
    request.user.pk = 4
    request.user.is_staff = True
    request.user.is_superuser = True
    response = toolbar(request=request, admin_site='admin')
    assert response.template_name == ['adminlinks/toolbar/user_4.js',
                                      'adminlinks/toolbar/superuser.js',
                                      'adminlinks/toolbar/staff.js',
                                      'adminlinks/toolbar/frontend.js']


def test_context(rf):
    request = rf.get('/', data={
        'include_html': True,
        'include_css': True,
        'js_namespace': 'django'
    })
    request.user = AnonymousUser()
    response = toolbar(request=request, admin_site='admin')
    assert 'toolbar_html' in response.context_data
    assert 'include_css' in response.context_data
    assert 'include_html' in response.context_data
    assert response.context_data['configuration'] == {
        'include_css': 1,
        'include_html': 1,
        'is_authenticated': 0,
        'js_namespace': 0
    }


def test_headers(rf):
    request = rf.get('/', data={
        'include_html': True,
        'include_css': True,
        'js_namespace': 'django'
    })
    request.user = AnonymousUser()
    response = toolbar(request=request, admin_site='admin')
    assert response.has_header('ETag') is True
    assert response.has_header('Expires') is True
    assert response.has_header('Cache-Control') is True
    assert response['Content-Type'] == 'application/javascript'
