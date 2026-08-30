from django.contrib import admin
from .models import ControlLimit

# Register your models here.
@admin.register(ControlLimit)
class ControlLimitAdmin(admin.ModelAdmin):
    list_display = ('variable', 'lower_limit', 'upper_limit')
    list_editable = ('lower_limit', 'upper_limit')
    search_fields = ('variable',)
