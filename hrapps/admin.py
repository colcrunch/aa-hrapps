from django.contrib import admin
from .models import Form


# Register your models here.
class FormAdmin(admin.ModelAdmin):
    list_select_related = True
    list_display = ('name', 'active', 'corporation','updated', 'created')
    list_filter = ('corporation__corporation_name','active')

    search_fields = ('name','corporation__corporation_name')

admin.site.register(Form, FormAdmin)