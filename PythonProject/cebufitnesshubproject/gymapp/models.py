from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager # Import AbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _ # For translating field names and help texts

# Create your models here.

# Custom Manager for our CustomUser
#Cruicial for creating users and superusers
# This is required when using AbstractBaseUser
# It defines how to create users and superusers
# You can customize this further as needed
class CustomUserManager(BaseUserManager):
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

# Custom user model
# Inheriting from AbstractBaseUser and PermissionsMixin
# AbstractBaseUser provides the core implementation of a user model, including hashed passwords and tokenized password resets.
# PermissionsMixin adds fields and methods for handling user permissions and groups.
# This allows us to define our own fields and authentication methods
# We will use email as the unique identifier instead of username
# We also add custom fields relevant to our gym application
class CustomUser(AbstractBaseUser, PermissionsMixin):
    # AbstractBaseUser provides:
    # password, last_login, is_active
    # PermissionsMixin provides:
    # is_superuser, groups, user_permissions

    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    
    # Custom fields from your previous MemberRegistration model
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
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    # Account freeze management
    is_frozen = models.BooleanField(default=False)
    # Freeze request tracking
    freeze_request_status = models.CharField(
        max_length=20,
        default='none',
        choices=(
            ('none', 'None'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('denied', 'Denied'),
        ),
    )
    freeze_requested_at = models.DateTimeField(null=True, blank=True)
    unfreeze_request_status = models.CharField(
        max_length=20,
        default='none',
        choices=(
            ('none', 'None'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('denied', 'Denied'),
        ),
    )
    unfreeze_requested_at = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager() # Use our custom manager

    USERNAME_FIELD = 'email' # Use email as the unique identifier for login
    REQUIRED_FIELDS = ['first_name', 'last_name'] # Fields required for creating a superuser

    class Meta:
        verbose_name = 'CustomUser'
        verbose_name_plural = 'CustomUsers'
        #db_table = 'my_gym_members' # Your custom table name

    def __str__(self):
        return self.email # Represent user by email

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name


# Gym Staff Model
# This model represents staff members who work at the gym
# Updated to match the exact ERD specification with only 5 attributes
class GymStaff(models.Model):
    # Staff ID (auto-generated)
    staff_id = models.AutoField(primary_key=True, help_text="Unique staff ID")
    
    # First Name
    first_name = models.CharField(max_length=100)
    
    # Last Name
    last_name = models.CharField(max_length=100)
    
    # Email
    email = models.EmailField(unique=True)
    
    # Phone Number
    phone_number = models.CharField(max_length=20)
    
    # Password (hashed)
    password = models.CharField(max_length=128, help_text="Hashed password")
    custom_user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    class Meta:
        verbose_name = 'Gym Staff'
        verbose_name_plural = 'Gym Staff'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} (ID: {self.staff_id})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"