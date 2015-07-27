# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
import json
import logging
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.template.base import Library
from adminlinks.utils import get_modeladmin_links
from adminlinks.utils import get_adminsite
from django.utils.safestring import mark_safe

register = Library()
logger = logging.getLogger(__name__)


def adminlinks_html(model, admin_site='admin'):
    template = "data-adminlinks-%(name)s='%(json)s'"
    bad_data = template % {'json': "{}", 'name': admin_site}
    site = get_adminsite(name=admin_site)
    if site is None:
        return bad_data
    # this should always get us the correct class (never ModelBase) on both
    # instances and classes themselves.
    safe_model = model._meta.model
    if safe_model not in site._registry:
        _error = "%(model)r class is not registered with %(admin)r" % {
            'model':model, 'admin':site}
        if settings.DEBUG:
            raise ValueError(_error)
        else:
            logger.debug(_error, exc_info=1)
            return bad_data

    modeladmin = site._registry[safe_model]
    # allow custom callables on the class ...
    call_kwargs = {'model': model, 'model_class': safe_model,
                   'modeladmin': modeladmin, 'admin': site}
    if hasattr(modeladmin, 'adminlinks'):
        data = modeladmin.adminlinks(**call_kwargs)
    else:
        data = get_modeladmin_links(**call_kwargs)
    return mark_safe(template % {'json': json.dumps(data, allow_nan=False,
                                                    separators=(',', ':'),
                                                    cls=DjangoJSONEncoder),
                                 'name': admin_site})
register.filter(name='adminlinks', filter_func=adminlinks_html)
