from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import CustomUser, gym_Member, GymStaff, Account_Request, Notification
from django.urls import reverse

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


@receiver(post_save, sender=Account_Request)
def create_request_notification(sender, instance, created, **kwargs):
    """
    Signal to notify all staff members when a new Account_Request is created.
    """
    # Only run if the request is NEW and its status is PENDING
    if created and instance.status == 'PENDING':
        # 1. Get all staff members
        all_staff = GymStaff.objects.all()
        
        # 2. Create the message
        member_name = instance.member.user.get_full_name()
        request_type = instance.get_request_type_display()
        message = f"New {request_type} request from {member_name}."
        
        # 3. Define the redirect URL
        # This points to your main staff dashboard, the 'Approval Queue' section
        redirect_url = reverse('staff_dashboard') + '#approvals' 

        # 4. Create a notification for each staff member
        for staff in all_staff:
            Notification.objects.create(
                recipient_staff=staff,
                message=message,
                notification_type='NEW_REQUEST',
                redirect_url=redirect_url
            )


#For the creation of the pending activation notification
@receiver(post_save, sender=gym_Member)
def create_registration_notification(sender, instance, created, **kwargs):
    """
    Signal to notify staff when a NEW member registers OR re-applies.
    """
    # Check for the temporary flag we set in the form
    is_reapplication = getattr(instance, '_is_reapplication', False)

    # Run if it's a brand new creation OR a re-application
    if created or is_reapplication:
        # 1. Get all staff
        all_staff = GymStaff.objects.all()
        
        # 2. Create message
        member_name = instance.user.get_full_name()
        
        # Custom message for re-applicants
        if is_reapplication:
            message = f"{member_name} has re-applied after rejection. Pending review."
        else:
            message = f"{member_name} has registered. Pending activation."
        
        # 3. Define URL
        redirect_url = reverse('staff_dashboard') + '?filter=pending'

        # 4. Create notifications
        for staff in all_staff:
            Notification.objects.create(
                recipient_staff=staff,
                message=message,
                notification_type='NEW_REGISTRATION',
                redirect_url=redirect_url,
                related_member=instance 
            )