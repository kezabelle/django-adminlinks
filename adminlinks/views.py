# -*- coding: utf-8 -*-


class ModelContext(object):
    """
    When working with things like :class:`~django.views.generic.list.ListView`,
    :class:`~django.views.generic.detail.DetailView` or anything else that acts
    on a single ``model`` type, it may be useful to be able to access that
    model in the template, specifically so that the
    :class:`~adminlinks.templatetags.adminlinks_buttons.Add` template tag
    may be used even when there is no actual instance of ``model`` available,
    given the class::

        class MyView(ModelContext, DetailView):
            model = MyModel

    it would now be possible to render the add button, even if there is no
    ``object`` in the context::

        {% load adminlinks_buttons %}
        <!-- model is not an instance, but a class -->
        {% render_add_button model %}

    In the slightly contrived example above, if the object didn't exist,
    :class:`~django.views.generic.detail.DetailView` would throw a
    :exc:`~django.http.Http404` anyway, but for demonstration purposes it should
    illustrate the purpose of ``ModelContext``
    """

    def get_context_data(self, **kwargs):
        """
        Puts the ``model`` into the template context.
        """
        if hasattr(self, 'model') and 'model' not in kwargs:
            kwargs['model'] = self.model
        return super(ModelContext, self).get_context_data(**kwargs)
