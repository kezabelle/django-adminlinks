# -*- coding: utf-8 -*-
from django.contrib.admin import helpers
from django.contrib.admin.util import unquote
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.models import fields_for_model
from django.http import Http404
from django.shortcuts import render_to_response
from django.utils.decorators import method_decorator
from django.utils.encoding import force_unicode
from django.utils.functional import update_wrapper
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import ugettext as _

csrf_protect_m = method_decorator(csrf_protect)

# Note: _popup is hilariously hard coded throughout the admin.
POPUP_VAR = '_popup'
FRONTEND_VAR = '_frontend_editing'

class AdminlinksMixin(object):
    frontend_editing = True

    def _get_wrap(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        return wrap


    def get_urls(self):
        original_urls = super(AdminlinksMixin, self).get_urls()
        from django.conf.urls.defaults import patterns, url
        wrap = self._get_wrap()
        info = self.model._meta.app_label, self.model._meta.module_name
        extra_urls = patterns('',
            url(r'^(.+)/change_field/(.+)/$',
            wrap(self.change_field_view),
            name='%s_%s_change_field' % info)
        )
        # extras have to come first, otherwise everything is gobbled by the
        # greedy nature of (.+) for the changelist view.
        return extra_urls + original_urls

    @csrf_protect_m
    @transaction.commit_on_success
    def change_field_view(self, request, object_id, fieldname, extra_context=None):
        """The 'change' admin view for this model."""
        model = self.model
        opts = model._meta

        obj = self.get_object(request, unquote(object_id))

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        all_fields = fields_for_model(obj)
        if fieldname not in all_fields:
            raise Http404(_('%(field)s does not exist on this object') % {'field': force_unicode(fieldname)})

        del all_fields[fieldname]
        fields_to_exclude = [k for k,v in all_fields.iteritems()]
        ModelForm = self.get_form(request, obj, exclude=fields_to_exclude, fields=[fieldname])
        # delete anything set on the self.form class explicitly.
        for field_to_exclude in fields_to_exclude:
            if field_to_exclude in ModelForm.base_fields:
                del ModelForm.base_fields[field_to_exclude]

        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=True)
            else:
                form_validated = False
                new_object = obj

            if form_validated:
                self.save_model(request, new_object, form, change=True)
                form.save_m2m()

                change_message = self.construct_change_message(request, form, formsets=None)
                self.log_change(request, new_object, change_message)
                return self.response_change(request, new_object)

        else:
            form = ModelForm(instance=obj)

        the_fieldset = [(None, {'fields': [fieldname]})]
        adminForm = helpers.AdminForm(form, the_fieldset, prepopulated_fields={},
            readonly_fields=None, model_admin=self)
        media = self.media + adminForm.media

        context = {
            'title': '', #_('Change %s') % force_unicode(obj),
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'show_delete': False,
            'is_popup': POPUP_VAR in request.REQUEST,
            'media': mark_safe(media),
            'errors': helpers.AdminErrorList(form, inline_formsets=[]),
            'root_path': getattr(self.admin_site, 'root_path', None),
            'app_label': opts.app_label,
            }
        context.update(extra_context or {})
        return self.render_change_form(request, context, obj=obj)

    def message_user(self, request, *args, **kwargs):
        if POPUP_VAR not in request.REQUEST or FRONTEND_VAR not in request.REQUEST:
            return super(AdminlinksMixin, self).message_user(request, *args, **kwargs)
        return None

    def get_success_templates(self, request):
        """
        Hook method to allow subclases to add or modify the templates provided
        in the case of a response.
        """
        app_label, model_name = self.model._meta.app_label, self.model._meta.object_name.lower()

        return [
            "adminlinks/%s/%s/success.html" % (app_label, model_name),
            "adminlinks/%s/success.html" % app_label,
            "adminlinks/success.html"
        ]

    def response_change(self, request, obj, *args, **kwargs):
        original_response = super(AdminlinksMixin, self).response_change(request, obj, *args, **kwargs)
        if POPUP_VAR not in request.REQUEST or FRONTEND_VAR not in request.REQUEST:
            return original_response
        context = {
            'action': {
                'add': False,
                'change': True,
                'delete': False,
                'as_string': 'change',
            },
            'object': {
                'pk': obj._get_pk_val(),
                'id': obj._get_pk_val(),
                'original': obj,
            }
        }
        context.update(self.get_response_change_context(request, obj))
        return render_to_response(self.get_success_templates(request), context)

    def response_add(self, request, obj, post_url_continue='../%s/'):
        original_response = super(AdminlinksMixin, self).response_add(request, obj, post_url_continue)
        if POPUP_VAR not in request.REQUEST or FRONTEND_VAR not in request.REQUEST:
            return original_response
        context = {
            'action': {
                'add': True,
                'change': False,
                'delete': False,
                'as_string': 'add',
            },
            'object': {
                'pk': obj._get_pk_val(),
                'id': obj._get_pk_val(),
                'original': obj,
            }
        }
        context.update(self.get_response_add_context(request, obj))
        return render_to_response(self.get_success_templates(request), context)

    def delete_view(self, request, object_id, extra_context=None):
        """Ridiculously, there's no response_delete method to patch, so instead
        we're just going to do a similar thing and hope for the best.
        """
        # silly Django, not providing the same variables to everything!
        our_extra_context = {'is_popup': POPUP_VAR in request.REQUEST}
        if extra_context is None:
            extra_context = {}
        extra_context.update(our_extra_context)
        resp = super(AdminlinksMixin, self).delete_view(request, object_id, extra_context)

        # Hijack the redirect on success to instead present our JS enabled template.
        if resp.status_code in (302,):
            context = {
                'action': {
                    'add': False,
                    'change': False,
                    'delete': True,
                    'as_string': 'delete',
                },
                'object': {
                    'pk': object_id,
                    'id': object_id,
                }
            }
            context.update(self.get_response_delete_context(request, object_id))
            resp = render_to_response(self.get_success_templates(request), context)
        return resp


    def history_view(self, request, *args, **kwargs):
        #import pdb; pdb.set_trace()
        # silly Django, not providing the same variables to everything!
        extra_context = {'is_popup': POPUP_VAR in request.REQUEST}
        if 'extra_context' in kwargs:
            extra_context.update(kwargs['extra_context'])
        kwargs['extra_context'] = extra_context
        return super(AdminlinksMixin, self).history_view(request, *args, **kwargs)

    def get_response_add_context(self, request, obj):
        return {}

    def get_response_change_context(self, request, obj):
        return {}

    def get_response_delete_context(self, request, obj_id):
        return {}
