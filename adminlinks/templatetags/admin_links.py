from django.template import Library
from django.core.urlresolvers import reverse, NoReverseMatch
from classytags.arguments import Argument, MultiKeywordArgument
from classytags.core import Options
from classytags.helpers import InclusionTag

register = Library()

class RequiresContextAuthMixin(object):
    def invalid_context(self, context, **kwargs):
        ''' we need a request in the context to get an authenticated user '''
        try:
            user = context['request'].user
        except (AttributeError, KeyError), e:
            return True
        
        if not user.is_authenticated() or not user.is_staff:
            return True

        return False

    def valid_context(self, context, **kwargs):
        return not self.invalid_context(context, **kwargs)
        
         
class ObjectEditAdmin(RequiresContextAuthMixin, InclusionTag):
    name = 'admin_edit'
    template = 'adminlinks/edit/link.html',
    options = Options(
        Argument('object', required=True),
        Argument('template', default=None, required=False),
    )

    def get_template(self, context, **kwargs):
        if not self.valid_context(context):
            return 'adminlinks/bad_context.html'
       
        opts = kwargs['object']._meta
        if not context['request'].user.has_perm(opts.app_label + '.' + opts.get_change_permission()):
            return 'adminlinks/bad_context.html'

        if kwargs['template'] is not None:
            return kwargs['template']

        return super(ObjectEditAdmin, self).get_template(context, **kwargs)
    
    def get_context(self, context, object, **kwargs):
        lookups = { 'app': object._meta.app_label, 'module': object._meta.module_name,}
        args = (object.pk,)
        new_ctx = {'type': object._meta.object_name}
        '''import pdb; pdb.set_trace()'''
        try:
            new_ctx.update(link=reverse(viewname='admin:%(app)s_%(module)s_change' % lookups, args=args))
        except NoReverseMatch:
            new_ctx.update(link=None)
        return new_ctx
        
class ObjectDeleteAdmin(InclusionTag):
    name = 'admin_delete'
    template = 'adminlinks/delete.html'
    options = Options(
        Argument('object', required=True),
        Argument('template', default='adminlinks/delete.html', required=False),
    )
    
    def get_context(self, context, object, template):
        lookups = { 'app': object._meta.app_label, 'module': object._meta.module_name,}
        args = (object.pk,)
        new_ctx = {'type': object._meta.object_name}
        try:
            new_ctx.update(link=reverse(viewname='admin:%(app)s_%(module)s_delete' % lookups, args=args))
            self.template = template
        except NoReverseMatch:
            new_ctx.update(link=None)
        return new_ctx

        
class ObjectListAdmin(InclusionTag):
    ''' Allow for the display of the link to an ... dunno yet? 
    
    Currently the implementation calls for usage as follows:
    {% load admin_links %}
    {% admin_list object %}
    {% admin_list queryset %}
    {% admin_list list_or_tuple %}
    '''

    name = 'admin_list'
    options = Options(
        Argument('object', required=True),
        MultiKeywordArgument('filters', resolve=False, required=False),
        Argument('template', default='adminlinks/list.html', required=False),
    )
    
    def get_context(self, context, object, filters, template):
        lookups = { 'app': object._meta.app_label, 'module': object._meta.module_name,}
        new_ctx = {'type': object._meta.object_name}
        try:
            new_ctx.update(link=reverse(viewname='admin:%(app)s_%(module)s_changelist' % lookups))
            self.template = template
        except NoReverseMatch:
            new_ctx.update(link=None)
        return new_ctx

        
class ObjectHistoryAdmin(InclusionTag):
    ''' Allow for the look-up and display of the link to an object's history
    
    Currently the implementation calls for usage as follows:
    {% load admin_links %}
    {% admin_history my_object_variable "custom/template.html" %}
    {% admin_history my_object_variable %}
    '''
    name = 'admin_history'
    options = Options(
        Argument('object', required=True),
        Argument('template', default='adminlinks/history.html', required=False),
    )
    
    def get_context(self, context, object, template):
        lookups = { 'app': object._meta.app_label, 'module': object._meta.module_name,}
        args = (object.pk,)
        new_ctx = {'type': object._meta.object_name}
        try:
            new_ctx.update(link=reverse(viewname='admin:%(app)s_%(module)s_history' % lookups, args=args))
            self.template = template
        except NoReverseMatch:
            new_ctx.update(link=None)
        return new_ctx

class ObjectAddAdmin(InclusionTag):
    name = 'admin_add'
    options = Options(
        Argument('object', required=True),
        Argument('template', default='adminlinks/history.html', required=False),
    )
    
    def get_context(self, context, object, template):
        return

register.tag(ObjectEditAdmin)
register.tag(ObjectDeleteAdmin)
register.tag(ObjectListAdmin)
register.tag(ObjectHistoryAdmin)
