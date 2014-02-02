# -*- coding: utf-8 -*-
from itertools import chain
import logging
from django.utils.html import escape

try:
    from django.utils.six.moves import urllib_parse
    urlsplit = urllib_parse.urlsplit
    urlunsplit = urllib_parse.urlunsplit
except (ImportError, AttributeError) as e:  # Python 2, < Django 1.5
    from urlparse import urlsplit, urlunsplit
from django.contrib.admin import helpers
from django.contrib.admin.options import csrf_protect_m
try:
    from django.contrib.admin.utils import unquote
except ImportError:  # < 1.7 ... pragma: no cover
    from django.contrib.admin.util import unquote
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.db import transaction
try:
    from django.db.transaction import atomic
except ImportError:
    from django.db.transaction import commit_on_success as atomic
from django.forms.models import fields_for_model
from django.http import Http404, QueryDict
from django.shortcuts import render_to_response
try:
    from django.utils.encoding import force_text
except ImportError:  # < Django 1.5
    from django.utils.encoding import force_unicode as force_text
try:
    # >=1.6
    import json
    from functools import update_wrapper
except ImportError as e:
    # <=1.5
    from django.utils import simplejson as json
    from django.utils.functional import update_wrapper

from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from adminlinks.changelist import AdminlinksChangeList
from adminlinks.constants import DATA_CHANGED, AUTOCLOSING


logger = logging.getLogger(__name__)


class AdminUrlWrap(object):
    """
    A minor helper for mixing into :class:`~django.contrib.admin.ModelAdmin`
    instances, exposing the url wrapping function used in the standard
    :meth:`~django.contrib.admin.ModelAdmin.get_urls`.
    """

    def _get_wrap(self):
        """
        Returns some magical decorated view that applies
        :meth:`~django.contrib.admin.AdminSite.admin_view` to a
        :class:`~django.contrib.admin.ModelAdmin` view::

            from django.contrib.admin import ModelAdmin

            class MyObj(AdminUrlWrap, ModelAdmin):

                def do_something(self):
                    wrapper = self._get_wrap()
                    wrapped_view = wrapper(self.my_custom_view)
                    return wrapped_view

        :return: a decorated view.
        """
        assert hasattr(self, 'admin_site') is True, "No AdminSite found ..."

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        return wrap


class AdminlinksMixin(AdminUrlWrap):
    """
    Our mixin, which serves two purposes:

    * Allows for per-field editing through the use of the use of
      :meth:`~adminlinks.admin.AdminlinksMixin.change_field_view`.

       * Per-field editing requires the *change* permission for the object.
       * Per-field editing is not exposed in the :class:`~django.contrib.admin.AdminSite`
         at all.
       * Per-field editing may be enabled in the frontend by using the
         :class:`~adminlinks.templatetags.adminlinks_buttons.EditField` template
         tag

    * Allows for the following views to be automatically closed on success,
      using a customisable template (see
      :meth:`~adminlinks.admin.AdminlinksMixin.get_success_templates` for how
      template discovery works.)

        * The add view (:meth:`~django.contrib.admin.ModelAdmin.add_view`)
        * The edit view (:meth:`~django.contrib.admin.ModelAdmin.change_view`)
        * The delete view (:meth:`~django.contrib.admin.ModelAdmin.delete_view`)
        * The edit-field view (
          :meth:`~adminlinks.admin.AdminlinksMixin.change_field_view`)

    """

    @csrf_protect_m
    @atomic
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
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_text(opts.verbose_name), 'key': escape(object_id)})

        all_fields = set(chain(fields_for_model(obj), self.form.base_fields))

        if fieldname not in all_fields:
            raise Http404(_('%(field)s does not exist on this object') % {'field': force_text(fieldname)})

        # if there are important fields, we'll assume they're denoted by a
        # leading underscore, like in treebeard

        fields_to_include = [x for x in all_fields
                             if x == fieldname or x.startswith('_')]
        fields_to_exclude = [x for x in all_fields
                             if x != fieldname and not x.startswith('_')]
        unique_together = frozenset(obj._meta.unique_together)
        if len(unique_together) > 0 and fieldname in unique_together:
            fields_to_include.extend(unique_together)
            fields_to_exclude = [x for x in fields_to_exclude
                                 if x not in unique_together]

        logger.debug("Excluding fields: {0!r}".format(fields_to_exclude))
        logger.debug("Including fields: {0!r}".format(fields_to_include))
        ModelForm = self.get_form(request, obj, exclude=fields_to_exclude,
                                  fields=fields_to_include)

        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=True)
            else:
                logger.debug('{cls!r} instance was invalid: {errors!r}'.format(
                    errors=form.errors, cls=form))
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

        the_fieldset = [
            (None, {
                'fields': [fieldname]}),
        ]
        remaining_fields = fields_to_include[:]
        remaining_fields.remove(fieldname)
        if remaining_fields:
            the_fieldset.append(
                (_("Other"), {
                    'fields': remaining_fields,
                    'classes': ['collapse']})
            )
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
            'is_popup': "_popup" in request.REQUEST,
        }
        context.update(extra_context or {})
        # tidy up after ourselves; by this point we don't need anything much ...
        # print(', '.join(locals().keys()))
        del (all_fields, adminForm, form, ModelForm, media, object_id,
             fields_to_exclude, fieldname, model, extra_context,
             the_fieldset, opts)
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
        del info
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
        del app_label, model_name, any_parents
        return templates

    def wants_to_autoclose(self, request):
        """
        .. versionadded:: 0.8.1

        :return: Whether or not ``_autoclose`` was in the request
        """
        return AUTOCLOSING in request.GET or AUTOCLOSING in request.POST

    def wants_to_continue_editing(self, request):
        """
        .. versionadded:: 0.8.1

        :return: Whether **Save** was pressed, or whether **Save and add
                 another/continue editing** was.
        """
        return any((
            '_continue' in request.POST,
            '_saveasnew' in request.POST,
            '_addanother' in request.POST
        ))

    def data_changed(self, querydict):
        """
        Can be passed things like request.GET, or just dictionaries, whatever.
        This is our magic querystring variable.

        .. versionadded:: 0.8.1
        """
        return DATA_CHANGED in querydict

    def should_autoclose(self, request):
        """

        .. versionadded:: 0.8.1

        :return: Whether or not ``_autoclose`` was in the request and whether
                 **Save** was pressed, or whether **Save and add
                 another/continue editing** was.
        """
        if self.wants_to_continue_editing(request):
            return False
        if self.wants_to_autoclose(request):
            return True
        return False

    def maybe_fix_redirection(self, request, response, obj=None):
        """
        This is a middleware-ish thing for marking whether a redirect needs
        to say data changed ... it's pretty complex, so has lots of comments.

        .. versionadded:: 0.8.1
        """
        # if there's no Location string, it's not even a redirect!
        if not response.has_header('location'):
            return response

        response.redirect_parts = list(urlsplit(response['Location']))
        querystring = QueryDict(response.redirect_parts[3], mutable=True)

        # if we got this far, we know:
        #   * it's a redirect (it has a Location header)
        #   * because it's a redirect, something has changed (been added/edited)
        #   * it may want to autoclose, but can't (because add another/continue
        #     editing was selected)

        # if the redirect doesn't already know that data has been changed,
        # fix that here.
        if not self.data_changed(querystring):
            # if the redirect:
            #   * is to a changelist view
            #   * the changelist view does not subclass AdminlinksChangeListMixin
            # then this will cause another redirect to e=1 which may lose
            # any other querystring parts. Need to look into a fix for this.
            # Possibly we can resolve() the response.redirect_parts[2]
            # and figure it out using tracks_querystring_keys?
            querystring.update({DATA_CHANGED: 1})

        # the view wanted to autoclose, but couldn't because
        # `wants_to_continue_editing` was True, so keep track of the desire
        # to autoclose, and maybe next time 'save' is hit it'll still be around
        # to do so.
        if self.wants_to_autoclose(request) and AUTOCLOSING not in querystring:
            querystring.update({AUTOCLOSING: 1})

        # should there be a `next` parameter, we'll treat it as canonical
        # override for any other action.
        if REDIRECT_FIELD_NAME in request.GET:
            next_url = request.GET[REDIRECT_FIELD_NAME]
            if (self.wants_to_continue_editing(request)
                    and REDIRECT_FIELD_NAME not in querystring):
                # save & add another, or save & continue editing was clicked
                # so we just presist the redirection location ...
                querystring.update({REDIRECT_FIELD_NAME: next_url})
            else:
                # `save` was pressed
                redir = unquote(next_url)
                if redir.startswith('/') and not redir.startswith('//'):
                    # patch the existing redirect with the *FINAL* data.
                    # also maintaining any querystring changes.
                    new_parts = list(urlsplit(redir))
                    # change path
                    if new_parts[2]:
                        response.redirect_parts[2] = new_parts[2]
                        response.canonical = True
                    # include querystring.
                    if new_parts[3]:
                        querystring.update(QueryDict(new_parts[3], mutable=False))

        response.redirect_parts[3] = querystring.urlencode()
        response['Location'] = urlunsplit(response.redirect_parts)
        return response

    def response_change(self, request, obj, *args, **kwargs):
        """
        Overrides the Django default, to try and provide a better experience
        for frontend editing when editing an existing object.
        """
        if self.should_autoclose(request):
            ctx_dict = self.get_response_change_context(request, obj)
            ctx_json = json.dumps(ctx_dict)
            context = {'data': ctx_dict, 'json': ctx_json}
            return render_to_response(self.get_success_templates(request),
                                      context)
        response = super(AdminlinksMixin, self).response_change(request, obj,
                                                                *args, **kwargs)
        return self.maybe_fix_redirection(request, response, obj)

    def response_add(self, request, obj, *args, **kwargs):
        """
        Overrides the Django default, to try and provide a better experience
        for frontend editing when adding a new object.
        """
        if self.should_autoclose(request):
            ctx_dict = self.get_response_add_context(request, obj)
            ctx_json = json.dumps(ctx_dict)
            context = {'data': ctx_dict, 'json': ctx_json}
            return render_to_response(self.get_success_templates(request),
                                      context)
        response = super(AdminlinksMixin, self).response_add(request, obj,
                                                             *args, **kwargs)
        return self.maybe_fix_redirection(request, response, obj)

    def delete_view(self, request, object_id, extra_context=None):
        """
        Overrides the Django default, to try and provide a better experience
        for frontend editing when deleting an object successfully.

        Ridiculously, there's no response_delete method to patch, so instead
        we're just going to do a similar thing and hope for the best.
        """
        response = super(AdminlinksMixin, self).delete_view(request, object_id,
                                                            extra_context)
        if self.should_autoclose(request) and response.status_code in (301, 302):
            ctx_dict = self.get_response_delete_context(request, object_id,
                                                        extra_context)
            ctx_json = json.dumps(ctx_dict)
            context = {'data': ctx_dict, 'json': ctx_json}
            response = render_to_response(self.get_success_templates(request),
                                          context)
            del context, ctx_dict, ctx_json
        return self.maybe_fix_redirection(request, response)

    def get_response_add_context(self, request, obj):
        """
        Provides a context for the template discovered by
        :meth:`~adminlinks.admin.AdminlinksMixin.get_success_templates`. Only
        used when we could reliably determine that the request was in our
        JavaScript modal window, allowing us to close it automatically.

        For clarity's sake, it should always return the minimum values
        represented here.

        :return: Data which may be given to a template.
                 Must be JSON serializable, so that a template may pass it
                 back to the browser's JavaScript engine.
        :rtype: a dictionary.
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
        Provides a context for the template discovered by
        :meth:`~adminlinks.admin.AdminlinksMixin.get_success_templates`. Only
        used when we could reliably determine that the request was in our
        JavaScript modal window, allowing us to close it automatically.

        For clarity's sake, it should always return the minimum values
        represented here.

        :return: Data which may be given to a template.
                 Must be JSON serializable, so that a template may pass it
                 back to the browser's JavaScript engine.
        :rtype: a dictionary.
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

    def get_response_delete_context(self, request, obj_id, extra_context):
        """
        Provides a context for the template discovered by
        :meth:`~adminlinks.admin.AdminlinksMixin.get_success_templates`. Only
        used when we could reliably determine that the request was in our
        JavaScript modal window, allowing us to close it automatically.

        For clarity's sake, it should always return the minimum values
        represented here.

        .. note::
            At the point this is called, the original object no longer exists,
            so we are stuck trusting the `obj_id` given as an argument.

        .. versionchanged::
            Introduced ``extra_context`` parameter.

        :return: Data which may be given to a template.
                 Must be JSON serializable, so that a template may pass it
                 back to the browser's JavaScript engine.
        :rtype: a dictionary.
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

    def get_changelist(self, request, **kwargs):
        """
        If the changelist hasn't been customised, lets just replace it with
        our own, which should allow us to track data changes without erroring.

        .. versionadded:: 0.8.1

        """
        cl = super(AdminlinksMixin, self).get_changelist(request, **kwargs)
        fits_requirements = (
            hasattr(cl, 'tracks_querystring_keys'),
            DATA_CHANGED in getattr(cl, 'tracks_querystring_keys', ())
        )
        if all(fits_requirements):
            return cl
        else:
            logger.warning('Custom `ChangeList` discovered,'
                           'AdminlinksChangeListMixin is being mixed in '
                           'automatically. Hopefully it will work!')
            cl = type('AutoPatchedChangeList', (AdminlinksChangeList, cl), {})
        return cl
