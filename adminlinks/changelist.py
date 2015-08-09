# -*- coding: utf-8 -*-
from django.contrib.admin.views.main import ChangeList
from adminlinks.constants import DATA_CHANGED


class AdminlinksChangeListMixin(object):
    """
    May be mixed in with any ChangeList implementation to
    remove *bad* querystring keys before they get to cause an
    ``IncorrectLookupParameters`` error.
    """
    tracks_querystring_keys = (DATA_CHANGED,)

    def get_queryset(self, *args, **kwargs):
        # this should stop the default ChangeList setting e=1 when we try
        # and set _data_changed=1 in the querystring.
        for x in self.tracks_querystring_keys:
            if x in self.params:
                del self.params[x]
        return super(AdminlinksChangeListMixin, self).get_queryset(*args, **kwargs)

    def get_query_set(self, *args, **kwargs):
        # this should stop the default ChangeList setting e=1 when we try
        # and set _data_changed=1 in the querystring.
        for x in self.tracks_querystring_keys:
            if x in self.params:
                del self.params[x]
        return super(AdminlinksChangeListMixin, self).get_query_set(*args, **kwargs)


class AdminlinksChangeList(AdminlinksChangeListMixin, ChangeList):
    """
    Default usable implementation which allows us to not error on discovering
    *invalid* (eg: DATA_CHANGED) fields in the querystring on the ChangeList.
    """
    pass
