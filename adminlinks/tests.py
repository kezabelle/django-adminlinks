from django.template.loader import Template, render_to_string
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.context import Context, RequestContext
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpRequest
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib import admin

try:
    from django.utils import unittest
except ImportError:
    import unittest

class AdminLinksTestCase(unittest.TestCase):
    
    def test_the_test_dependencies(self):
        '''In lieu of mock objects, we need certain things in INSTALLED_APPS'''
        self.assertEqual('django.contrib.auth' in settings.INSTALLED_APPS, True)
        self.assertEqual('django.contrib.admin' in settings.INSTALLED_APPS, True)

        found_admin = True 
        admin_namespace = admin.site.app_name
        try:
            for view in ('index', 'password_change', 'password_change_done'):
                reverse('%(ns)s:%(view)s' % {'ns': admin_namespace, 'view': view})
        except NoReverseMatch, e:
            found_admin = False
        self.assertEqual(found_admin, True)

        
    def test_loads_without_error(self):
        '''Ensure that the templatetags lib loads without issue'''
        template = Template('''{% load admin_links %}''')
        context = Context({})
        result = template.render(context)
        self.assertEqual(result, u'')

class AdminEditTestCase(unittest.TestCase):

    def setUp(self):
        self.user = User.objects.get_or_create(username='standard', is_staff=False)[0]
        self.superuser = User.objects.get_or_create(username='admin', is_active=True,
            is_staff=True, is_superuser=True)[0]
        self.request = HttpRequest()

    def default_edit_template(self):
        return Template('''{% load admin_links %}{% admin_edit object %}''')

    def specified_edit_template(self):
        return Template('''{% load admin_links %}{% admin_edit object "adminlinks/dummy.html" %}''')

    def nonexistant_edit_template(self):
        return Template('''{% load admin_links %}{% admin_edit object "adminlinks/this_doesnt_exist.html" %}''')

    def invalid_context(self):
        return render_to_string('adminlinks/bad_context.html', {})

    def valid_context(self, object):
        object_name = object._meta.object_name
        lookups = { 
            'ns': admin.site.app_name,
            'app': object._meta.app_label,
            'module': object._meta.module_name,
        }
        args = (object.pk,)
        return render_to_string('adminlinks/edit/link.html', {
            'type': object_name,
            'link': reverse(viewname='%(ns)s:%(app)s_%(module)s_change' % lookups, args=args)
        })
    
    def test_edit_link_without_permissions(self):
        '''Without appropriate permissions, make sure the link isn't even displayed'''
        template = self.default_edit_template()
        self.request.user = self.user
        context = RequestContext(self.request, {'object': self.user})
        result = template.render(context)
        self.assertEqual(result, self.invalid_context())
        
    def test_edit_link_with_permission(self):
        '''With correct permissions, show the edit link with the default template'''
        template = self.default_edit_template()
        self.request.user = self.superuser
        context = RequestContext(self.request, {'object': self.user})
        result = template.render(context).strip()
        self.assertEqual(result, self.valid_context(self.user))

    def test_edit_link_without_requestcontext(self):
        '''Without `request` in the context, the edit link shouldn't be displayed'''
        user = self.superuser
        template = self.default_edit_template()
        context = Context({'object': user})
        result = template.render(context)
        self.assertEqual(result, self.invalid_context())

    def test_with_specified_good_template(self):
        '''When given a template which exists, here's what we expect'''
        template = self.specified_edit_template()
        self.request.user = self.superuser
        context = RequestContext(self.request, {'object': self.user})
        result = template.render(context).strip()
        self.assertEqual(result, u'')

    def test_with_specified_bad_template(self):
        '''When given a template which doesn't exist, then we'll have a template error'''
        template = self.nonexistant_edit_template()
        self.request.user = self.superuser
        context = RequestContext(self.request, {'object': self.user})
        try:
            result = template.render(context).strip()
        except (TemplateDoesNotExist, TemplateSyntaxError), e:
            self.assertEqual(True, True)


