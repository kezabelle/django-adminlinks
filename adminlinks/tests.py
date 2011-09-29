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
        '''Make sure the environment can support the tests. '''
        # Check that both the built-in auth and admin apps are available.
        self.assertEqual('django.contrib.auth' in settings.INSTALLED_APPS, True)
        self.assertEqual('django.contrib.admin' in settings.INSTALLED_APPS, True)

        # For the tests (and the app!) to work, we need to know that the admin
        # is mounted in the urlconf, and what name the default one is under
        # (typically, 'admin') - I'm using a boolean to test for if anything
        # goes wrong, because unittest prior to python 2.7 / Django 1.3 doesn't
        # have methods for asserting exceptions are raised.
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
        # This test is the first port of call to ensure there's no silly errors
        # in the templatetags lib that might prevent it loading (syntax errors,
        # I'm looking at you!)
        template = Template('''{% load admin_links %}''')
        context = Context({})
        result = template.render(context)
        # Should be blank, because we're not doing anything.
        self.assertEqual(result, u'')

class SingleObjectTestBase(object):

    def setUp(self):
        self.request = HttpRequest()
        # a normal, boring user
        self.user = User.objects.get_or_create(username='standard', is_staff=False)[0]
        # someone who /can/ access the admin, and has permissions
        self.superuser = User.objects.get_or_create(username='admin', is_active=True,
            is_staff=True, is_superuser=True)[0]

    def default_template(self, type):
        return Template('{%% load admin_links %%}{%% admin_%s object %%}' % type)

    def specified_template(self, type):
        return Template('{%% load admin_links %%}{%% admin_%s object "adminlinks/dummy.html" %%}' % type)

    def nonexistant_template(self, type):
        return Template('{%% load admin_links %%}{%% admin_%s object "adminlinks/this_doesnt_exist.html" %%}' % type)

    def invalid_context(self):
        ''' Utility method for comparing a templatetag's test output to what we expect '''
        return render_to_string('adminlinks/bad_context.html', {})

    def valid_context(self, object, type, urlpart):
        ''' Simulated call to the templatetag for comparison to it's actual output '''
        object_name = object._meta.object_name
        lookups = { 
            'ns': admin.site.app_name,
            'app': object._meta.app_label,
            'module': object._meta.module_name,
            'url': urlpart,
        }
        args = (object.pk,)
        return render_to_string('adminlinks/%s_link.html' % type, {
            'type': object_name,
            'link': reverse(viewname='%(ns)s:%(app)s_%(module)s_%(url)s' % lookups, args=args)
        })
    
    def without_permission(self, type):
        template = self.default_template(type)
        self.request.user = self.user
        context = RequestContext(self.request, {'object': self.user})
        result = template.render(context)
        self.assertEqual(result, self.invalid_context())
        
    def with_permission(self, type, urlpart):
        template = self.default_template(type)
        self.request.user = self.superuser
        context = RequestContext(self.request, {'object': self.user})
        result = template.render(context)
        self.assertEqual(result, self.valid_context(self.user, type, urlpart))

    def without_requestcontext(self, type):
        user = self.superuser
        template = self.default_template(type)
        context = Context({'object': user})
        result = template.render(context)
        self.assertEqual(result, self.invalid_context())

    def with_specified_good_template(self, type):
        template = self.specified_template(type)
        self.request.user = self.superuser
        context = RequestContext(self.request, {'object': self.user})
        result = template.render(context)
        # Note: it's supposed to be blank because it uses a dummy template,
        # where everything else does not.
        self.assertEqual(result, u'')

    def with_specified_bad_template(self, type):
        template = self.nonexistant_template(type)
        self.request.user = self.superuser
        context = RequestContext(self.request, {'object': self.user})
        # The template system will provide a TemplateSyntaxError, whose underlying
        # type was TemplateDoesNotExist. Catching both should ensure that we
        # got an error where we expected one.
        try:
            result = template.render(context)
        except (TemplateDoesNotExist, TemplateSyntaxError), e:
            self.assertEqual(True, True)


class AdminSingleObjectTestCase(SingleObjectTestBase, unittest.TestCase):
    def test_link_without_permissions(self):
        '''Without appropriate permissions, make sure the link isn't even displayed'''
        self.without_permission('edit')
        self.without_permission('history')
        self.without_permission('delete')

    def test_link_with_permission(self):
        '''With correct permissions, show the link with the default template'''
        self.with_permission('edit', 'change')
        self.with_permission('history', 'history')
        self.with_permission('delete', 'delete')

    def test_link_without_requestcontext(self):
        '''Without `request` in the context, the link shouldn't be displayed'''
        self.without_requestcontext('edit')
        self.without_requestcontext('history')
        self.without_requestcontext('delete')

    def test_with_specified_good_template(self):
        '''When given a template which exists, here's what we expect'''
        self.with_specified_good_template('edit') 
        self.with_specified_good_template('history') 
        self.with_specified_good_template('delete') 
    
    def test_with_specified_bad_template(self):
        '''When given a template which doesn't exist, then we'll have a template error'''
        self.with_specified_bad_template('edit')
        self.with_specified_bad_template('history')
        self.with_specified_bad_template('delete')

