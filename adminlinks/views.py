# -*- coding: utf-8 -*-
import hashlib
import json
from adminlinks.forms import JavascriptOptions
from adminlinks.utils import get_adminsite, _get_template_context
from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.cache import patch_response_headers
from django.utils.cache import patch_cache_control
from django.utils.encoding import force_text
from django.views.decorators.http import require_http_methods


@require_http_methods(['GET', 'HEAD'])
def toolbar(request, admin_site):
    site = get_adminsite(admin_site)
    if site is None:
        raise Http404("Invalid admin site name: %(site)s" % {'site': admin_site})

    options = JavascriptOptions(data=request.GET or {}, files=None, initial={})
    if not options.is_valid():
        raise Http404("%(form)s got invalid arguments: %(errors)r" % {
            'form': options.__class__, 'errors': options.errors})

    if not hasattr(request, 'user'):
        raise Http404("Cannot get the user from the request. Missing the "
                      "middleware?")

    possible_templates = ['adminlinks/toolbar/anonymous.js']
    if request.user.is_authenticated():
        possible_templates.insert(0, 'adminlinks/toolbar/authenticated.js')
        if request.user.is_staff:
            possible_templates.insert(0, 'adminlinks/toolbar/staff.js')
        if request.user.is_superuser:
            possible_templates.insert(0, 'adminlinks/toolbar/superuser.js')
        if request.user.pk:
            possible_templates.insert(0, 'adminlinks/toolbar/user_{}.js'.format(str(request.user.pk)))  # noqa


    if options.cleaned_data.get('include_html'):
        toolbar_html_context = _get_template_context(request=request,
                                                     admin_site=admin_site)
        toolbar_html = render_to_string("adminlinks/toolbar.html", context={
            'adminlinks': toolbar_html_context,
            'user': request.user,
        })
    else:
        toolbar_html = ''

    fragment_html_context = {
         'url': '{{ url }}',
         'title': '{{ title }}',
         'namespace': '{{ namespace }}',
     }
    fragment_html = ''.join(render_to_string(
        'adminlinks/toolbar_fragment.html', context=fragment_html_context).splitlines())  # noqa
    context = {
        'admin_site': admin_site,
        'site': site,
        'toolbar_html': json.dumps(toolbar_html)[1:-1],
        'fragment_html': json.dumps(fragment_html)[1:-1],
        'possible_templates': possible_templates,
    }
    context.update(**options.cleaned_data)
    response = render(request, template_name=possible_templates, context=context,
                      content_type='application/javascript')
    hashable = '%(pk)s-%(data)s' % {
        'pk': force_text(request.user.pk),
        'data': response.content,
    }
    response['ETag'] = '"%s"' % hashlib.md5(hashable).hexdigest()
    patch_response_headers(response=response,
                           cache_timeout=settings.CACHE_MIDDLEWARE_SECONDS)
    patch_cache_control(response=response, must_revalidate=True,
                        max_age=settings.CACHE_MIDDLEWARE_SECONDS)
    return response
