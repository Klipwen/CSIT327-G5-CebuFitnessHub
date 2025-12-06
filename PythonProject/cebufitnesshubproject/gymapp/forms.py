from django import forms
from django.core.exceptions import ValidationError
# Corrected import to include all models
from .models import CustomUser, gym_Member, GymStaff, Account_Request
from django.contrib.auth.password_validation import validate_password
import re

# CustomUserRegistrationForm remains unchanged as it correctly targets CustomUser 
# this is where we can see the validation functions of the registration
class CustomUserRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(
        label='First Name',
        min_length=2,
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your first name', 'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Last Name',
        min_length=2,
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your last name', 'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Email',
        max_length=255,
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email', 'class': 'form-control'})
    )
    contact_number = forms.CharField(
        label='Contact Number',
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your phone number', 'class': 'form-control'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password', 'class': 'form-control'}),
        help_text='Password must be at least 8 characters long and contain letters and numbers.'
    )
    password_confirm = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password', 'class': 'form-control'})
    )
    emergency_contact_name = forms.CharField(
        label='Emergency Contact Name',
        min_length=2,
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter emergency contact name', 'class': 'form-control'})
    )
    emergency_contact_number = forms.CharField(
        label='Emergency Contact Number',
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter contact number', 'class': 'form-control'})
    )
    medical_conditions = forms.CharField(
        label='Medical Conditions (Optional)',
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={'placeholder': 'Please list any medical conditions...', 'class': 'form-control'})
    )
    fitness_goals = forms.CharField(
        label='Fitness Goals (Optional)',
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={'placeholder': 'What are your fitness goals?', 'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = (
            'first_name', 'last_name', 'email', 'contact_number',
            'emergency_contact_name', 'emergency_contact_number',
            'medical_conditions', 'fitness_goals',
            'password', 'password_confirm'
        )

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name and not re.match(r"^[a-zA-Z\s\-']+$", first_name):
            raise ValidationError("First name contains invalid characters.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name and not re.match(r"^[a-zA-Z\s\-']+$", last_name):
            raise ValidationError("Last name contains invalid characters.")
        return last_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # We strictly check format here, but we moved the "Unique" check to clean()
        # to handle the "Instance Swap" logic safely.
        return email

    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number')
        if contact_number:
            cleaned_digits = ''.join(filter(str.isdigit, contact_number))
            if not cleaned_digits:
                raise ValidationError("Please enter your contact number.")
            if len(cleaned_digits) < 10 or len(cleaned_digits) > 15:
                raise ValidationError("Contact number must be between 10 and 15 digits.")
        return contact_number

    def clean_emergency_contact_name(self):
        emergency_contact_name = self.cleaned_data.get('emergency_contact_name')
        if emergency_contact_name and not re.match(r"^[a-zA-Z\s]+$", emergency_contact_name):
            raise ValidationError("Emergency contact name contains invalid characters.")
        return emergency_contact_name

    def clean_emergency_contact_number(self):
        emergency_contact_number = self.cleaned_data.get('emergency_contact_number')
        if emergency_contact_number:
            cleaned_digits = ''.join(filter(str.isdigit, emergency_contact_number))
            if not cleaned_digits:
                raise ValidationError("Please enter your emergency contact number.")
            if len(cleaned_digits) < 10 or len(cleaned_digits) > 15:
                raise ValidationError("Emergency contact number must be between 10 and 15 digits.")
        return emergency_contact_number

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        email = cleaned_data.get('email')

        # 1. Password Matching Validation
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match.")
        
        if password and not self.errors.get('password'):
            try:
                validate_password(password, user=None)
            except ValidationError as e:
                self.add_error('password', e)

        # 2. "Rejected User Recycling" Logic
        if email:
            existing_user = CustomUser.objects.filter(email=email).first()
            
            if existing_user:
                # Check if they are REJECTED (Safe to overwrite)
                if hasattr(existing_user, 'gym_member') and existing_user.gym_member.activation_status == 'rejected':
                    # [THE MAGIC FIX]
                    # We swap the form's instance to the existing user.
                    # This tells Django: "We are UPDATING this user, not creating a new one."
                    self.instance = existing_user
                
                # Check if they are ACTIVE or PENDING (Block them)
                else:
                    # This provides your custom error message
                    self.add_error('email', "An account with this email address already exists.")

        return cleaned_data

    def save(self, commit=True):
        # Because we swapped 'self.instance' in clean(), 
        # super().save() automatically handles both CREATING new users 
        # and UPDATING existing rejected users.
        
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_active = False 

        if commit:
            user.save()
            
            # Check if this user has an existing profile (Case A: Re-application)
            if hasattr(user, 'gym_member'):
                member = user.gym_member
                
                # If they were rejected, flag this as a re-application for the signal
                if member.activation_status == 'rejected':
                    # --- THIS IS THE TRANSIENT FLAG ---
                    member._is_reapplication = True 
                    # --- END FLAG ---

                member.activation_status = 'pending' # Move them back to Pending list
                member.save() # This triggers the signal
            
            # Case B: New User (Create profile)
            else:
                # The signal in create_user_profile will handle the initial creation
                gym_Member.objects.get_or_create(user=user)

        return user

# MemberLoginForm remains unchanged
class MemberLoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        max_length=255,
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email address', 'class': 'form-control'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password', 'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            try:
                user = CustomUser.objects.get(email=email)
                
                if not user.check_password(password):
                    # Error 1: Wrong password
                    raise ValidationError("Invalid password.")
                    
                if not user.is_active:
                    # Error 2: Inactive account
                    raise ValidationError("This account is inactive and awaiting staff activation.")
                    
                # Success!
                cleaned_data['user'] = user
                
            except CustomUser.DoesNotExist:
                # Error 3: User does not exist
                raise ValidationError("Invalid account.")
                
        return cleaned_data

# PasswordChangeForm remains unchanged
class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter current password'})
    )
    new_password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter a new password'})
    )
    confirm_password = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new password'})
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(PasswordChangeForm, self).__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        user = self.request.user
        if not user.check_password(current_password):
            raise ValidationError("Current password is incorrect.")
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', "New passwords do not match.")
        
        if new_password:
            try:
                validate_password(new_password, user=self.request.user)
            except ValidationError as e:
                self.add_error('new_password', e)
        return cleaned_data

# FreezeRequestForm remains unchanged
class FreezeRequestForm(forms.Form):
    duration = forms.ChoiceField(
        label='Duration (Days)',
        choices=[(i, f"{i} Day{'s' if i > 1 else ''}") for i in range(1, 6)],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        help_text="You can freeze your account for 1 to 5 days."
    )
    reason = forms.CharField(
        label='Reason',
        widget=forms.Textarea(attrs={'placeholder': 'Please provide a brief reason for your request...'}),
        min_length=10,
        required=True,
    )

# UnfreezeRequestForm remains unchanged
class UnfreezeRequestForm(forms.Form):
    reason = forms.CharField(
        label='Reason (Optional)',
        widget=forms.Textarea(attrs={'placeholder': 'You can provide a brief reason for your request...'}),
        required=False
    )