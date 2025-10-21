from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, GymStaff
# from .forms import StaffRegistrationForm  # Commented out - form needs to be updated for new model structure

# Custom User Admin
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'contact_number')}),
        ('Emergency Contact', {'fields': ('emergency_contact_name', 'emergency_contact_number')}),
        ('Additional Info', {'fields': ('medical_conditions', 'fitness_goals')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_superuser', 'is_active'),
        }),
    )

    # Disable admin log entries to avoid FK constraint pointing at auth_user
    def log_addition(self, request, object, message):
        return

    def log_change(self, request, object, message):
        return

    def log_deletion(self, request, object, object_repr):
        return

# Gym Staff Admin - Updated to match exact ERD specification
@admin.register(GymStaff)
class GymStaffAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'get_full_name', 'email', 'phone_number')
    search_fields = ('staff_id', 'first_name', 'last_name', 'email', 'phone_number')
    ordering = ('staff_id',)
    readonly_fields = ('staff_id',)
    
    fieldsets = (
        ('Staff Information', {
            'fields': ('staff_id', 'first_name', 'last_name', 'email', 'phone_number', 'password')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Hash the password if it's being set
        if 'password' in form.changed_data:
            from django.contrib.auth.hashers import make_password
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)
    
    def has_add_permission(self, request):
        # Only allow superusers to add staff
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        # Only allow superusers to change staff
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        # Only allow superusers to delete staff
        return request.user.is_superuser
    
    def log_addition(self, request, object, message):
        # Disable admin logging to prevent foreign key constraint errors
        pass
    
    def log_change(self, request, object, message):
        # Disable admin logging to prevent foreign key constraint errors
        pass
    
    def log_deletion(self, request, object, object_repr):
        # Disable admin logging to prevent foreign key constraint errors
        pass
