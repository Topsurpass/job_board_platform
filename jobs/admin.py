from django.contrib import admin
from .models import Job, Category, Application

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    list_filter = ('created_by',)
    search_fields = ('name', 'created_by')

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'type', 'location', 'category')
    list_filter = ('category','type', 'posted_by', 'is_active')
    search_fields = ('title', 'company', 'location')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'applicant', 'applied_at')
    list_filter = ('job', 'applied_at')
    search_fields = ('job',)