# -*- coding: utf-8 -*-


class ModelContext(object):
    """
    A mixin for providing the model type to the template context, useful for
    rendering add buttons which would otherwise need to be passed an actual
    instance ...
    """
    def get_context_data(self, **kwargs):
        if hasattr(self, 'model') and 'model' not in kwargs:
            kwargs['model'] = self.model
        return super(ModelContext, self).get_context_data(**kwargs)
