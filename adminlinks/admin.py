# -*- coding: utf-8 -*-
import logging
from django.contrib.admin import helpers, AdminSite
from django.contrib.admin.options import csrf_protect_m
from django.contrib.admin.util import unquote
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.models import fields_for_model
from django.http import Http404
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.utils.encoding import force_unicode
from django.utils.functional import update_wrapper
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _


logger = logging.getLogger(__name__)


class AdminUrlWrap(object):
    def _get_wrap(self):
        assert hasattr(self, 'admin_site') is True, "No AdminSite found ..."

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        return wrap


class AdminlinksMixin(AdminUrlWrap):

    @csrf_protect_m
    @transaction.commit_on_success
    def change_field_view(self, request, object_id, fieldname, extra_context=None):
        """
        Allows a user to view a form with only one field (named in the URL args)
        to edit. All others are ignored.
        """
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
        fields_to_exclude = [k for k, v in all_fields.items()]
        ModelForm = self.get_form(request, obj, exclude=fields_to_exclude,
                                  fields=[fieldname])
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

                change_message = self.construct_change_message(request, form,
                                                               formsets=None)
                self.log_change(request, new_object, change_message)
                return self.response_change(request, new_object)

        else:
            form = ModelForm(instance=obj)

        the_fieldset = [(None, {'fields': [fieldname]})]
        adminForm = helpers.AdminForm(form, the_fieldset, prepopulated_fields={},
                                      readonly_fields=None, model_admin=self)
        media = self.media + adminForm.media

        context = {
            'title': '',
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'show_delete': False,
            'media': mark_safe(media),
            'errors': helpers.AdminErrorList(form, inline_formsets=[]),
            'root_path': getattr(self.admin_site, 'root_path', None),
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, obj=obj)

    def get_urls(self):
        urls = super(AdminlinksMixin, self).get_urls()
        from django.conf.urls import url
        info = self.model._meta.app_label, self.model._meta.module_name
        # add change_field view into our URLConf
        urls.insert(0, url(
            regex=r'^(?P<object_id>.+)/change_field/(?P<fieldname>[\w_]+)/$',
            view=self._get_wrap()(self.change_field_view),
            name='%s_%s_change_field' % info)
        )
        return urls

    def get_success_templates(self, request):
        """
        Forces the attempted loading of the following:
            - a template for this model.
            - a template for this app.
            - a template for any parent model.
            - a template for any parent app.
            - a guaranteed to exist template (the base success file)

        :param request: The WSGIRequest
        :return: list of strings representing templates to look for.
        """
        app_label = self.model._meta.app_label
        model_name = self.model._meta.object_name.lower()
        any_parents = self.model._meta.parents.keys()
        templates = [
            "adminlinks/%s/%s/success.html" % (app_label, model_name),
            "adminlinks/%s/success.html" % app_label,
        ]
        for parent in any_parents:
            app_label = parent._meta.app_label
            model_name = parent._meta.object_name.lower()
            templates.extend([
                "adminlinks/%s/%s/ssuccess.html" % (app_label, model_name),
                "adminlinks/%s/success.html" % app_label,
            ])
        templates.extend(['adminlinks/success.html'])
        return templates

    def response_change(self, request, obj, *args, **kwargs):
        """
        Overrides the Django default, to try and provide a better experience
        for frontend editing when editing an existing object.

        .. seealso:: :meth:`~adminlinks.admin.SuccessResponses.get_success_templates`
        """
        if '_autoclose' in request.REQUEST:
            ctx_dict = self.get_response_change_context(request, obj)
            ctx_json = simplejson.dumps(ctx_dict)
            context = {'data': ctx_dict, 'json': ctx_json}
            return render_to_response(self.get_success_templates(request),
                                      context)
        return super(AdminlinksMixin, self).response_change(request, obj,
                                                            *args, **kwargs)

    def response_add(self, request, obj, post_url_continue='../%s/'):
        """
        Overrides the Django default, to try and provide a better experience
        for frontend editing when adding a new object.

        .. seealso:: :meth:`~adminlinks.admin.SuccessResponses.get_success_templates`
        """
        if '_autoclose' in request.REQUEST:
            ctx_dict = self.get_response_add_context(request, obj)
            ctx_json = simplejson.dumps(ctx_dict)
            context = {'data': ctx_dict, 'json': ctx_json}
            return render_to_response(self.get_success_templates(request),
                                          context)
        return super(AdminlinksMixin, self).response_add(request, obj,
                                                         post_url_continue)

    def delete_view(self, request, object_id, extra_context=None):
        """
        Ridiculously, there's no response_delete method to patch, so instead
        we're just going to do a similar thing and hope for the best.

        .. seealso:: :meth:`~adminlinks.admin.SuccessResponses.get_response_delete_context`
        .. seealso:: :meth:`~adminlinks.admin.SuccessResponses.get_success_templates`
        """
        response = super(AdminlinksMixin, self).delete_view(request, object_id,
                                                            extra_context)
        if '_autoclose' in request.REQUEST and response.status_code in (301, 302):
            ctx_dict = self.get_response_delete_context(request, object_id)
            ctx_json = simplejson.dumps(ctx_dict)
            context = {'data': ctx_dict, 'json': ctx_json}
            response = render_to_response(self.get_success_templates(request),
                                          context)
        return response

    def get_response_add_context(self, request, obj):
        """
        .. seealso:: :meth:`~adminlinks.admin.SuccessResponses.response_add`
        """
        return {
            'action': {
                'add': True,
                'change': False,
                'delete': False,
            },
            'object': {
                'pk': obj._get_pk_val(),
                'id': obj._get_pk_val(),
            }
        }

    def get_response_change_context(self, request, obj):
        """
        .. seealso:: :meth:`~adminlinks.admin.SuccessResponses.response_change`
        """
        return {
            'action': {
                'add': False,
                'change': True,
                'delete': False,
            },
            'object': {
                'pk': obj._get_pk_val(),
                'id': obj._get_pk_val(),
            }
        }

    def get_response_delete_context(self, request, obj_id):
        """
        .. seealso:: :meth:`~adminlinks.admin.SuccessResponses.delete_view`
        """
        return {
            'action': {
                'add': False,
                'change': False,
                'delete': True,
            },
            'object': {
                'pk': obj_id,
                'id': obj_id,
            }
        }
