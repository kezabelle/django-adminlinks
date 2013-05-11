# -*- coding: utf-8 -*-
from django.contrib.admin import helpers
from django.contrib.admin.options import csrf_protect_m
from django.contrib.admin.util import unquote
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.models import fields_for_model
from django.http import Http404
from django.shortcuts import render_to_response
from django.utils.encoding import force_unicode
from django.utils.functional import update_wrapper
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from adminlinks.constants import POPUP_QS_VAR, FRONTEND_QS_VAR


class AllowMorePopups(object):
    """
    We want to be able to show the delete view without the standard Django
    header etc, unfortunately Django doesn't allow for this, and apparently
    won't; see https://code.djangoproject.com/ticket/20302

    As a result, we just extend whatever `extra_context` is given, to
    include the desired context variable.
    """
    def delete_view(self, request, object_id, extra_context=None):
        """
        Adds key `is_popup` to the context, via `extra_context`.
        Must check `request.REQUEST` because we don't know if we've been
        POSTed to through the confirmation.
        """
        extra_context = extra_context or {}
        extra_context.update(is_popup=POPUP_QS_VAR in request.REQUEST)
        return super(AllowMorePopups, self).delete_view(request, object_id, extra_context)

    def history_view(self, request, object_id, extra_context=None):
        """
        Adds key `is_popup` to the context, via `extra_context`
        """
        extra_context = extra_context or {}
        extra_context.update(is_popup=POPUP_QS_VAR in request.GET)
        return super(AllowMorePopups, self).history_view(request, object_id, extra_context)


class HideMessages(object):
    """
    If we're in a popup, it's useless to message the user, as they won't see it
    in the admin, and *may* see it in the frontend if the site uses the messages
    framework. As such, we're just going to ignore it, for consistency's sake.
    """
    def message_user(self, request, *args, **kwargs):
        if POPUP_QS_VAR not in request.REQUEST or FRONTEND_QS_VAR not in request.REQUEST:
            return super(HideMessages, self).message_user(request, *args, **kwargs)
        return None


class ChangeFieldView(object):
    """
    Adds a new view onto ModelAdmin objects, enabling a user to edit only
    a single field at a time.
    """
    def _get_wrap(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        return wrap

    def get_urls(self):
        """
        Monkey patch the existing URLs and put our change field view on first,
        so that changelist view doesn't greedily absorb it.

        :return: a list of url :func:`~django.conf.urls.patterns`
        :rtype: :data:`list`
        """
        original_urls = super(SuccessResponses, self).get_urls()
        from django.conf.urls.defaults import patterns, url
        wrap = self._get_wrap()
        info = self.model._meta.app_label, self.model._meta.module_name
        url_regex = r'^(?P<object_id>.+)/change_field/(?P<fieldname>\w+)/$'
        extra_urls = patterns('',
                              url(url_regex, wrap(self.change_field_view),
                                  name='%s_%s_change_field' % info))
        # extras have to come first, otherwise everything is gobbled by the
        # greedy nature of (.+) for the changelist view.
        return extra_urls + original_urls

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
            'is_popup': POPUP_QS_VAR in request.REQUEST,
            'media': mark_safe(media),
            'errors': helpers.AdminErrorList(form, inline_formsets=[]),
            'root_path': getattr(self.admin_site, 'root_path', None),
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, obj=obj)


class SuccessResponses(object):
    """
    Because Django doesn't offer the exact hooks we need, this class exists
    to handle responses from inside a popup, where we ideally don't want to
    redirect or otherwise present the original response.
    """

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
            "adminlinks/%ssuccess.html" % app_label,
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
        original_response = super(SuccessResponses, self).response_change(request, obj, *args, **kwargs)
        if POPUP_QS_VAR not in request.REQUEST or FRONTEND_QS_VAR not in request.REQUEST:
            return original_response
        context = {}
        context.update(self.get_response_change_context(request, obj))
        return render_to_response(self.get_success_templates(request), context)

    def response_add(self, request, obj, post_url_continue='../%s/'):
        response = super(SuccessResponses, self).response_add(request, obj, post_url_continue)
        if (POPUP_QS_VAR not in request.REQUEST
                and response.status_code > 300 and response.status_code < 400):
            return response
        context = {}
        context.update(self.get_response_add_context(request, obj))
        return render_to_response(self.get_success_templates(request), context)

    def delete_view(self, request, object_id, extra_context=None):
        """
        Ridiculously, there's no response_delete method to patch, so instead
        we're just going to do a similar thing and hope for the best.
        """
        resp = super(SuccessResponses, self).delete_view(request, object_id, extra_context)

        # Hijack the redirect on success to instead present our JS enabled template.
        if resp.status_code in (302,):
            context = {}
            context.update(self.get_response_delete_context(request, object_id))
            resp = render_to_response(self.get_success_templates(request), context)
        return resp

    def get_response_add_context(self, request, obj):
        """
        .. seealso:: :meth:`adminlinks.admin.SuccessResponses.response_add`
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
                'original': obj,
            }
        }

    def get_response_change_context(self, request, obj):
        """
        .. seealso:: :meth:`adminlinks.admin.SuccessResponses.response_change`
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
                'original': obj,
            }
        }

    def get_response_delete_context(self, request, obj_id):
        """
        .. seealso:: :meth:`adminlinks.admin.SuccessResponses.delete_view`
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


class AdminlinksMixin(HideMessages, AllowMorePopups, ChangeFieldView, SuccessResponses):
    """
    An object whose sole purposes is to facilitate all the combined functionality
    provided by the classes it inherits from.

    .. seealso:: :class:`~adminlinks.admin.HideMessages`
    .. seealso:: :class:`~adminlinks.admin.AllowMorePopups`
    .. seealso:: :class:`~adminlinks.admin.ChangeFieldView`
    .. seealso:: :class:`~adminlinks.admin.SuccessResponses`
    """
    pass
