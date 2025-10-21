from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, GymStaff

@receiver(post_save, sender=CustomUser)
def create_or_update_gym_staff(sender, instance, created, **kwargs):
    """
    Create or update a GymStaff profile whenever a CustomUser is saved.
    Syncs core fields into Supabase via Django ORM.
    """
    if instance.is_staff:
        GymStaff.objects.update_or_create(
            custom_user=instance,
            defaults={
                'email': instance.email,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
                'phone_number': instance.contact_number or '',
                'password': instance.password,
            }
        )