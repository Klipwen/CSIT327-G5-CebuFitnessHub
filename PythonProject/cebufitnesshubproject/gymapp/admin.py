from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser,
    gym_Member,
    GymStaff,
    Account_Request,
    Billing_Record,
    Check_In,
    Activity_Log,
    Notification,
    ClassSchedule,
    OCCUPANCY_TRACKER
)

# --- Profile Inlines ---
# This allows you to see the "profile" data (Member or Staff)
# directly on the CustomUser's admin page.

class gym_MemberInline(admin.StackedInline):
    """Shows the gym_Member profile data inside the CustomUser admin page."""
    model = gym_Member
    can_delete = False
    verbose_name_plural = 'Member Profile'
    # Show the member-specific fields
    fields = ('balance', 'monthly_fee', 'next_due_date', 'is_frozen')

class GymStaffInline(admin.StackedInline):
    """Shows the GymStaff profile data inside the CustomUser admin page."""
    model = GymStaff
    can_delete = False
    verbose_name_plural = 'Staff Profile'
    # This model has no extra fields, so it will just show the link

# --- Custom User Admin ---

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    This is the main admin interface for ALL users (Members and Staff).
    It correctly displays fields from CustomUser and includes the
    appropriate profile inline.
    """
    # Fields to display in the main user list
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'is_superuser')
    
    # Fields for the "Edit" page
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': (
            'first_name',
            'last_name',
            'contact_number',
            'emergency_contact_name',
            'emergency_contact_number',
            'medical_conditions',
            'fitness_goals'
        )}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Fields for the "Add User" page
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            # You had password1/password2 here, but UserAdmin's add form
            # handles password creation automatically. We just need to
            # define the fields for our CustomUser.
            'fields': ('email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active'),
        }),
    )
    
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    # This dynamically adds the correct profile (Member or Staff)
    def get_inlines(self, request, obj=None):
        if obj:
            if obj.is_staff:
                return (GymStaffInline,)
            else:
                return (gym_MemberInline,)
        return ()

# --- Register Other Models ---

@admin.register(Account_Request)
class AccountRequestAdmin(admin.ModelAdmin):
    list_display = ('member', 'request_type', 'status', 'request_date', 'staff_reviewer')
    list_filter = ('status', 'request_type')
    search_fields = ('member__user__email',) # Correctly search the related user's email

@admin.register(Billing_Record)
class BillingRecordAdmin(admin.ModelAdmin):
    list_display = ('member', 'transaction_type', 'amount', 'timestamp', 'staff_processor')
    list_filter = ('transaction_type',)
    search_fields = ('member__user__email',)

@admin.register(Check_In)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ('member', 'check_in_time', 'check_out_time')
    search_fields = ('member__user__email',)

@admin.register(Activity_Log)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('member', 'activity_date', 'duration_minutes')
    search_fields = ('member__user__email',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient_staff', 'notification_type', 'message', 'is_read', 'timestamp')
    list_filter = ('is_read', 'notification_type')

@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'instructor_name', 'day_of_week', 'start_time', 'end_time', 'location')
    list_filter = ('day_of_week', 'instructor_name')

@admin.register(OCCUPANCY_TRACKER)
class OccupancyTrackerAdmin(admin.ModelAdmin):
    list_display = ('current_count', 'capacity_limit', 'last_updated')

# We don't need to register gym_Member or GymStaff separately
# because they are handled as "inlines" on the CustomUserAdmin.