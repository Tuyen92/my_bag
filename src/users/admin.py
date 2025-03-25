from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile
from companies.models import Company

# Define the inline for UserProfile
class UserProfileInline(admin.StackedInline):  # Or TabularInline for a different layout
    model = UserProfile
    fields = ('company', 'is_admin')  # Customize the fields you want to display
    extra = 1  # Add an extra empty form for user to create new UserProfile

# Register the User model and add the UserProfileInline
class CustomUserAdmin(UserAdmin):
    # Add inline UserProfile to User admin page
    inlines = [UserProfileInline]
    
    # Optional: Customize the User model fields displayed in the admin
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active')

# Re-register the User model with the custom UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
