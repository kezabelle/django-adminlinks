# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from django.forms import Form
from django.forms.fields import ChoiceField, NullBooleanField
from django.forms.widgets import RadioSelect


class JavascriptOptions(Form):
    js_namespace = ChoiceField(choices=(
        ('dollar', "jQuery bound to window"),
        ('django', "jQuery bound to the Django namespace"),
    ), required=False, initial='dollar')
    # Both of these use RadioSelect because it offers a better set of possible
    # true/false values. CheckboxInput is utter crap.
    # Also they're NullBoolean so that the absence of their key in request.GET
    # can be indicated by the time we get to our custom cleaning.
    include_html = NullBooleanField(required=False, initial=True, widget=RadioSelect)
    include_css = NullBooleanField(required=False, initial=True, widget=RadioSelect)

    def clean_js_namespace(self):
        choices = {
            'dollar': 'window.$',
            'django': 'django.jQuery',
        }
        initial = self.fields['js_namespace'].initial
        value = self.cleaned_data.get('js_namespace') or initial
        return choices[value]

    def clean_include_html(self):
        value = self.cleaned_data.get('include_html')
        return value is None or value is True

    def clean_include_css(self):
        value = self.cleaned_data.get('include_css')
        return value is None or value is True
