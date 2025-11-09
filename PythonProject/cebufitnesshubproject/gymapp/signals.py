from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import CustomUser, gym_Member, GymStaff

# Use settings.AUTH_USER_MODEL to refer to your CustomUser
# This is safer than importing CustomUser directly
User = settings.AUTH_USER_MODEL 

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create a gym_Member or GymStaff profile
    when a new CustomUser is created.
    """
    if created: # Only run on creation
        if instance.is_staff:
            # If the new user is staff, create a GymStaff profile
            GymStaff.objects.create(user=instance)
        else:
            # If the new user is not staff, create a gym_Member profile
            gym_Member.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to save the profile whenever the CustomUser is saved.
    """
    try:
        if instance.is_staff:
            # Check if the profile exists before saving
            if hasattr(instance, 'gym_staff'):
                instance.gym_staff.save()
        else:
            # Check if the profile exists before saving
            if hasattr(instance, 'gym_member'):
                instance.gym_member.save()
    except (gym_Member.DoesNotExist, GymStaff.DoesNotExist):
        # This can happen if a user is created before the signal was connected
        # or if is_staff was changed on an existing user.
        # We re-run the creation logic just in case.
        if not hasattr(instance, 'gym_staff') and not hasattr(instance, 'gym_member'):
             create_user_profile(sender, instance, created=True, **kwargs)