from django.contrib import admin
from adminlinks.admin import AdminlinksMixin
from myapp.models import MyModel

# At it's most simple, mixing in with the default modeladmin.
class MyModelAdmin(AdminlinksMixin, admin.ModelAdmin):
    list_display = ['my_field', 'my_other_field']
admin.site.register(MyModel, MyModelAdmin)

################################################################################

from django.contrib import admin
from adminlinks.admin import AdminlinksMixin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

# Replacing an existing Modeladmin
try:
    admin.site.unregister(User)
except admin.NotRegistered:
    pass

class MyUserAdmin(AdminlinksMixin, UserAdmin):
    pass
admin.site.register(User, MyUserAdmin)


