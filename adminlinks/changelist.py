# -*- coding: utf-8 -*-
from django.contrib.admin.views.main import ChangeList
from adminlinks.constants import DATA_CHANGED


class AdminlinksChangeListMixin(object):
    tracks_querystring_keys = (DATA_CHANGED,)

    def tracks_querystring_key(self, key):
        return key in self.tracks_querystring_keys


    def get_query_set(self, *args, **kwargs):
        # this should stop the default ChangeList setting e=1 when we try
        # and set _data_changed=1 in the querystring.
        if DATA_CHANGED in self.params:
            del self.params[DATA_CHANGED]
        return super(AdminlinksChangeListMixin, self).get_query_set(*args,
                                                                    **kwargs)


class AdminlinksChangeList(AdminlinksChangeListMixin, ChangeList):
    """
    Default usable implementation
    """
    pass
