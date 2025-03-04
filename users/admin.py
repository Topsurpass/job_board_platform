from django.contrib import admin
from .models import User, UserProfile, EmployerProfile

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email','first_name', 'role')
    list_filter = ('role',)
    search_fields = ('email',)

    # To be fixed for subsequent updates
    def save_model(self, request, obj, form, change):
        """Ensure password is hashed when created via admin dashboard"""
        if "password" in form.cleaned_data and form.cleaned_data["password"]:
            if obj.pk:
                if not obj.check_password(form.cleaned_data["password"]):  
                    obj.set_password(form.cleaned_data["password"])
            else:
                obj.set_password(form.cleaned_data["password"])

        super().save_model(request, obj, form, change)

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

