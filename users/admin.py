from django.contrib import admin
from .models import User, UserProfile, EmployerProfile

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'role')
    list_filter = ('role',)
    search_fields = ('email',)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_filter = ('user', 'id')

@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_filter = ('user',)
