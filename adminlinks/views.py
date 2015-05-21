# -*- coding: utf-8 -*-
import json
from adminlinks.forms import JavascriptOptions
from adminlinks.utils import get_adminsite, _get_template_context
from django.http import Http404
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache

@never_cache
def toolbar(request, admin_site):
    site = get_adminsite(admin_site)
    if site is None:
        raise Http404("Invalid admin site name: %(site)s" % {'site': admin_site})

    options = JavascriptOptions(data=request.GET or {}, files=None, initial={})
    if not options.is_valid():
        raise Http404("%(form)s got invalid arguments: %(errors)r" % {
            'form': options.__class__, 'errors': options.errors})


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
    return render(request, template_name=possible_templates, context=context,
                  content_type='application/javascript')


class ModelContext(object):
    """
    When working with things like :class:`~django.views.generic.list.ListView`,
    :class:`~django.views.generic.detail.DetailView` or anything else that acts
    on a single ``model`` type, it may be useful to be able to access that
    model in the template, specifically so that the
    :class:`~adminlinks.templatetags.adminlinks_buttons.Add` template tag
    may be used even when there is no actual instance of ``model`` available,
    given the class::

        class MyView(ModelContext, DetailView):
            model = MyModel

    it would now be possible to render the add button, even if there is no
    ``object`` in the context::

        {% load adminlinks_buttons %}
        <!-- model is not an instance, but a class -->
        {% render_add_button model %}

    In the slightly contrived example above, if the object didn't exist,
    :class:`~django.views.generic.detail.DetailView` would throw a
    :exc:`~django.http.Http404` anyway, but for demonstration purposes it should
    illustrate the purpose of ``ModelContext``
    """

    def get_context_data(self, **kwargs):
        """
        Puts the ``model`` into the template context.
        """
        if hasattr(self, 'model') and 'model' not in kwargs:
            kwargs['model'] = self.model
        return super(ModelContext, self).get_context_data(**kwargs)
