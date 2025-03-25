from django.contrib import admin
from .models import Company  # Import your Company model
from users.models import UserProfile


class UserProfileInline(admin.TabularInline):  # Or admin.StackedInline
    model = UserProfile
    extra = 1  # Number of empty forms to show


# Register the Company model
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'location', 'postal_code', 'created_date')  # Fields to display in the list view
    search_fields = ('name', 'address')  # Fields to search in the admin
    list_filter = ('location',)  # Filters for the list view
    ordering = ('name',)  # Default ordering of the list
    
    # Optional: Add fields for the form view for creating/editing
    fields = ('name', 'address', 'location', 'postal_code', 'email', 'logo')  # Fields to show in the form view
    readonly_fields = ('id',)  # Make the id field read-only
    inlines = [UserProfileInline]  # Add inline model for UserProfile
