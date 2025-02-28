from django.contrib import admin
from .models import Job, Industry, Category

@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    list_filter = ('created_by',)
    search_fields = ('name', 'created_by')
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    list_filter = ('created_by','industry',)
    search_fields = ('name', 'created_by')

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'type', 'location', 'industry')
    list_filter = ('industry','type', 'posted_by', 'is_active')
    search_fields = ('title', 'company', 'location')