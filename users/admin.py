from django.contrib import admin
from .models import User, UserProfile, EmployerProfile

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email','first_name', 'role')
    list_filter = ('role',)
    search_fields = ('email',)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user','location', 'experience_level')
    list_filter = ('location', 'experience_level')
    search_fields = ('email',)


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ('user','company_location')
    list_filter = ('user',)
    search_fields = ('email',)

