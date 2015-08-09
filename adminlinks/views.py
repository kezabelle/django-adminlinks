# -*- coding: utf-8 -*-
import hashlib
import json
from adminlinks.forms import JavascriptOptions
from adminlinks.utils import get_adminsite, _get_template_context
from django.conf import settings
from django.http import Http404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.utils.cache import patch_response_headers
from django.utils.cache import patch_cache_control
from django.utils.encoding import force_text
from django.views.decorators.http import require_http_methods


def bool_to_int(x):
    return 1 if x is True else 0


def templates(user):
    possible_templates = ['adminlinks/toolbar/frontend.js']
    if user.is_staff:
        possible_templates.insert(0, 'adminlinks/toolbar/staff.js')
    if user.is_superuser:
        possible_templates.insert(0, 'adminlinks/toolbar/superuser.js')
    if user.pk:
        possible_templates.insert(0, 'adminlinks/toolbar/user_{}.js'.format(str(user.pk)))  # noqa
    return possible_templates


@require_http_methods(['GET', 'HEAD'])
def toolbar(request, admin_site):
    site = get_adminsite(admin_site)
    if site is None:
        raise Http404("Invalid admin site name: %(site)s" % {'site': admin_site})

    if not hasattr(request, 'user'):
        raise Http404("Cannot get the user from the request. Missing the "
                      "middleware?")

    options = JavascriptOptions(data=request.GET or {}, files=None, initial={})
    if not options.is_valid():
        raise Http404("%(form)s got invalid arguments: %(errors)r" % {
            'form': options.__class__, 'errors': options.errors})

    possible_templates = templates(user=request.user)

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

    cleaned_data_ints = {k: bool_to_int(v)
                         for k, v in options.cleaned_data.items()}

    context = {
        'admin_site': admin_site,
        'site': site,
        'toolbar_html': json.dumps(toolbar_html)[1:-1],
        'fragment_html': json.dumps(fragment_html)[1:-1],
        'possible_templates': possible_templates,
        'configuration': dict({
            'is_authenticated': bool_to_int(request.user.is_authenticated()),
        }, **cleaned_data_ints),
    }
    context.update(**options.cleaned_data)

    response = TemplateResponse(request, template=possible_templates,
                                context=context, content_type='application/javascript')
    hashable = '%(pk)s-%(data)s' % {
        'pk': force_text(request.user.pk),
        'data': response.rendered_content,
    }
    response['ETag'] = '"%s"' % hashlib.md5(hashable).hexdigest()
    patch_response_headers(response=response,
                           cache_timeout=settings.CACHE_MIDDLEWARE_SECONDS)
    patch_cache_control(response=response, must_revalidate=True,
                        max_age=settings.CACHE_MIDDLEWARE_SECONDS)
    return response
