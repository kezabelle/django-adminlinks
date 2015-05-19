from adminlinks.urls import adminlinks_toolbar_url
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.shortcuts import render


def index(request):
    usermodel = get_user_model()
    usermodel.do_not_call_in_templates = True
    made_users = False
    made_superusers = False
    if not usermodel.objects.exists():
        made_users = True
        for index in range(1, 20):
            usermodel.objects.create(username='user{}'.format(index),
                                     is_staff=False,
                                     is_superuser=False)
    if not usermodel.objects.filter(is_superuser=True).exists():
        made_superusers = True
        superuser = usermodel(username='admin', is_staff=True,
                              is_superuser=True)
        superuser.set_password('admin')
        superuser.save()

    return render(request, template_name=[
        'index.html',
    ], context={
        'made_users': made_users,
        'usermodel': usermodel,
        'users': usermodel.objects.all(),
        'made_superusers': made_superusers,
    })


urlpatterns = [
    adminlinks_toolbar_url,
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', index),
]
