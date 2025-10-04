from django.db import models

# Create your models here.

class MemberRegistration(models.Model):
    
    #Model representing a pending member registration request.
    #Fields capture all necessary information for initial sign-up.

    # Database Fields 
    memberID = models.AutoField(primary_key=True) 
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=20)
    
    # Note on Password: This field holds the raw password initially. 
    # Best practice is to handle password hashing/saving logic 
    # within a custom form's save() method or the view/serializer 
    # before saving to the database.
    password = models.CharField(max_length=255)
    confirm_password = models.CharField(max_length=255)
    emergency_contact_name = models.CharField(max_length=255)
    emergency_contact_number = models.CharField(max_length=20)
    
    # Optional fields
    medical_conditions = models.TextField(blank=True, null=True)
    fitness_goals = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    # The class Meta block and the __str__ method have been removed as requested.
