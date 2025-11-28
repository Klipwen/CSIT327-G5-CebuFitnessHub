from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings # Used for Foreign Keys to CustomUser

# --- 1. CORE USER MODELS ---

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password) # Handles password hashing
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Corrected CustomUser model.
    All freeze/unfreeze fields have been REMOVED as they now
    belong in the Account_Request model.
    """
    # AbstractBaseUser provides: password, last_login
    # PermissionsMixin provides: is_superuser, groups, user_permissions

    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    
    # Custom fields from ERD
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_number = models.CharField(max_length=20, blank=True, null=True)
    medical_conditions = models.TextField(blank=True, null=True)
    fitness_goals = models.TextField(blank=True, null=True)

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'DesignD-esignates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    # --- All freeze/unfreeze fields have been REMOVED ---

    objects = CustomUserManager() # Use our custom manager

    USERNAME_FIELD = 'email' # Use email as the unique identifier for login
    REQUIRED_FIELDS = ['first_name', 'last_name'] # Fields required for creating a superuser

    class Meta:
        verbose_name = 'CustomUser'
        verbose_name_plural = 'CustomUsers'

    def __str__(self):
        return self.email

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

class gym_Member(models.Model):
    """
    Profile for a non-staff user (is_staff=False).
    Holds member-specific financial and status data.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='gym_member'
    )
    # ERD Fields
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    next_due_date = models.DateField(null=True, blank=True)
    
    # This field will be controlled by staff via Account_Request logic
    is_frozen = models.BooleanField(default=False)

    # Stores the remaining days of the plan when frozen
    days_remaining_on_freeze = models.IntegerField(null=True, blank=True)
    # --- END OF NEW FIELD ---

    membership_id = models.CharField(max_length=20, unique=True, null=True, blank=True, help_text="e.g., CFH-2025-0001")

    # --- ADD THIS NEW FIELD ---This allows us to distinguish between a "fresh" registration (Pending) and one that you have explicitly denied (Rejected).
    ACTIVATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    activation_status = models.CharField(
        max_length=10, 
        choices=ACTIVATION_STATUS_CHOICES, 
        default='pending'
    )
    # --- END ADD ---

    class Meta:
        verbose_name = 'Gym Member Profile'
        verbose_name_plural = 'Gym Member Profiles'

    def __str__(self):
        return f"Member Profile for {self.user.email}"

class GymStaff(models.Model):
    """
    Corrected, lean profile for a staff user (is_staff=True).
    The redundant fields are gone; they are all accessed
    via the 'user' link.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='gym_staff'
    )
    # The ERD shows no other attributes.
    # If you need staff-specific fields (e.g., 'job_title'), add them here.

    class Meta:
        verbose_name = 'Gym Staff Profile'
        verbose_name_plural = 'Gym Staff Profiles'

    def __str__(self):
        return f"Staff Profile for {self.user.email}"


# --- 2. TRANSACTIONAL AND LOG ENTITIES ---

class Account_Request(models.Model):
    """
    NEW MODEL
    Handles member requests for account changes (e.g., Freeze/Unfreeze).
    This correctly implements the ERD logic.
    """
    REQUEST_TYPE_CHOICES = [
        ('FREEZE', 'Freeze Account'),
        ('UNFREEZE', 'Unfreeze Account'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    request_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(gym_Member, on_delete=models.CASCADE, related_name='account_requests')
    staff_reviewer = models.ForeignKey(GymStaff, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')
    
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPE_CHOICES)
    reason = models.TextField(blank=True, null=True)
    request_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    
    staff_decision_reason = models.TextField(blank=True, null=True)
    decision_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_request_type_display()} request for {self.member.user.email} ({self.status})"

class Billing_Record(models.Model):
    """
    NEW MODEL
    Records all financial transactions (payments, fees, adjustments).
    """
    TRANSACTION_CHOICES = [
        ('PAYMENT', 'Payment'),
        ('FEE', 'Membership Fee'),
        ('ADJUSTMENT', 'Adjustment'),
    ]

    billing_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(gym_Member, on_delete=models.PROTECT, related_name='billing_records')
    staff_processor = models.ForeignKey(GymStaff, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_billings')
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_transaction_type_display()} of {self.amount} for {self.member.user.email}"

class Check_In(models.Model):
    """
    NEW MODEL
    Logs member check-in and check-out times.
    """
    checkin_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(gym_Member, on_delete=models.CASCADE, related_name='check_ins')
    check_in_time = models.DateTimeField(default=timezone.now)
    check_out_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-check_in_time']

    def __str__(self):
        return f"Check-in for {self.member.user.email} at {self.check_in_time}"

class Activity_Log(models.Model):
    """
    NEW MODEL
    Logs member workout duration, derived from Check_In data.
    """
    activity_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(gym_Member, on_delete=models.CASCADE, related_name='activity_logs')
    activity_date = models.DateField()
    duration_minutes = models.IntegerField()

    class Meta:
        ordering = ['-activity_date']

    def __str__(self):
        return f"Activity for {self.member.user.email} on {self.activity_date} ({self.duration_minutes} mins)"


# --- 3. SUPPORTING AND STANDALONE ENTITIES ---

class Notification(models.Model):
    """
    NEW MODEL
    Stores notifications for staff members (e.g., new pending request).
    """
    notification_id = models.AutoField(primary_key=True)
    recipient_staff = models.ForeignKey(GymStaff, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=50) # e.g., 'NEW_REQUEST', 'PAYMENT_DUE'
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    redirect_url = models.CharField(max_length=255, blank=True, null=True, help_text="URL to redirect to on click")

    related_member = models.ForeignKey('gym_Member', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Notification for {self.recipient_staff.user.email} ({self.notification_type})"

class ClassSchedule(models.Model):
    """
    NEW MODEL
    Standalone table for the weekly class schedule.
    """
    DAY_CHOICES = [
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
        (7, 'Sunday'),
    ]

    class_id = models.AutoField(primary_key=True)
    class_name = models.CharField(max_length=100)
    instructor_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']
        verbose_name = 'Class Schedule'
        verbose_name_plural = 'Class Schedules'

    def __str__(self):
        return f"{self.class_name} with {self.instructor_name} on {self.get_day_of_week_display()}"

class OCCUPANCY_TRACKER(models.Model):
    """
    Standalone table for tracking live gym occupancy and global settings.
    This table will likely only ever have one row.
    """
    occupancy_id = models.AutoField(primary_key=True)
    current_count = models.IntegerField(default=0)
    capacity_limit = models.IntegerField(default=100) # Added default
    peak_hours_start = models.TimeField(default='08:00') # Added default
    peak_hours_end = models.TimeField(default='20:00') # Added default
    last_updated = models.DateTimeField(default=timezone.now)

    # --- ADD THESE NEW FIELDS ---
    gym_name = models.CharField(max_length=100, default='Cebu Fitness Hub')
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    contact_address = models.CharField(max_length=255, blank=True, null=True)
    default_monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=2000.00)
    member_id_prefix = models.CharField(max_length=5, default='CFH')
    # --- END OF NEW FIELDS ---

    class Meta:
        verbose_name = 'Occupancy Tracker'
        verbose_name_plural = 'Occupancy Trackers'

    def __str__(self):
        return f"Current Occupancy: {self.current_count}/{self.capacity_limit}"

"""
    new model
    """