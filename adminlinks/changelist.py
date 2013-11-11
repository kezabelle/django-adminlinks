# -*- coding: utf-8 -*-
from django.contrib.admin.views.main import ChangeList
from adminlinks.constants import DATA_CHANGED


class AdminlinksChangeListMixin(object):
    """
    May be mixed in with any
    :class:`~django.contrib.admin.views.main.ChangeList` implementation to
    remove *bad* querystring keys before they get to cause an
    ``IncorrectLookupParameters`` error.

    .. versionadded:: 0.8.1
    """
    tracks_querystring_keys = (DATA_CHANGED,)

    def get_query_set(self, *args, **kwargs):
        # this should stop the default ChangeList setting e=1 when we try
        # and set _data_changed=1 in the querystring.
        for x in self.tracks_querystring_keys:
            if x in self.params:
                del self.params[x]
        return super(AdminlinksChangeListMixin, self).get_query_set(*args,
                                                                    **kwargs)


class AdminlinksChangeList(AdminlinksChangeListMixin, ChangeList):
    """
    Default usable implementation which allows us to not error on discovering
    *invalid* (eg: :attr:`~adminlinks.constnats.DATA_CHANGED`) fields in the
    querystring on the ChangeList.

    .. versionadded:: 0.8.1
    """
    pass
