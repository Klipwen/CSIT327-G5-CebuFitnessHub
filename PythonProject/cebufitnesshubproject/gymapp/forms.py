from django import forms
from django.core.exceptions import ValidationError
from .models import CustomUser  # Import your custom user model
from django.contrib.auth.password_validation import validate_password
import regex  # We'll use this for all regular expressions

# Custom user registration form
# Inheriting from forms.ModelForm to leverage model field definitions and validations
# This also helps in reducing redundancy and ensures consistency with the model
# We will add custom validation and widgets as needed
# Note: Since we are using AbstractBaseUser, we need to define all fields explicitly
# including password fields, as ModelForm won't automatically create these for AbstractBaseUser without customization.
# We will also handle password hashing in the save method
# We will add custom validation for password strength and matching
# Additionally, we will add validation for contact numbers to ensure they are in a valid format
class CustomUserRegistrationForm(forms.ModelForm):
    # ====================================================================
    # WHAT'S ADDED/MODIFIED: first_name field definition
    # USE: Enforces required, min_length, max_length at the field level.
    #      The regex character restriction is handled in clean_first_name.
    # ====================================================================
    first_name = forms.CharField(
        label='First Name',
        min_length=2,          # Added: Minimum length requirement
        max_length=50,         # Added: Maximum length requirement
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your first name', 'class': 'form-control'})
    )
    # ====================================================================
    # WHAT'S ADDED/MODIFIED: last_name field definition
    # USE: Enforces required, min_length, max_length at the field level.
    #      The regex character restriction is handled in clean_last_name.
    # ====================================================================
    last_name = forms.CharField(
        label='Last Name',
        min_length=2,          # Added: Minimum length requirement
        max_length=50,         # Added: Maximum length requirement
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your last name', 'class': 'form-control'})
    )

    # Email field definition remains the same
    email = forms.EmailField(
        label='Email',
        max_length=255,
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email', 'class': 'form-control'})
    )

    # ====================================================================
    # WHAT'S ADDED/MODIFIED: contact_number field definition
    # USE: Enforces required at the field level.
    #      The specific 10-15 digit format is handled in clean_contact_number.
    # ====================================================================
    contact_number = forms.CharField(
        label='Contact Number',
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your phone number', 'class': 'form-control'})
    )

    # ====================================================================
    # WHAT'S ADDED/MODIFIED: password field definition
    # USE: Standard password input, min_length & password validators are in settings.py and clean method.
    # ====================================================================
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password', 'class': 'form-control'}),
        help_text='Password must be at least 8 characters long and contain letters and numbers.'
    )
    # ====================================================================
    # WHAT'S ADDED/MODIFIED: password_confirm field definition
    # USE: For password matching check in clean method.
    # ====================================================================
    password_confirm = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password', 'class': 'form-control'})
    )

    # ====================================================================
    # WHAT'S ADDED/MODIFIED: emergency_contact_name field definition
    # USE: Enforces required, min_length, max_length at the field level.
    #      The regex character restriction is handled in clean_emergency_contact_name.
    # ====================================================================
    emergency_contact_name = forms.CharField(
        label='Emergency Contact Name',
        min_length=2,
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter emergency contact name', 'class': 'form-control'})
    )

    # ====================================================================
    # WHAT'S ADDED/MODIFIED: emergency_contact_number field definition
    # USE: Enforces required at the field level.
    #      The specific 10-15 digit format is handled in clean_emergency_contact_number.
    # ====================================================================
    emergency_contact_number = forms.CharField(
        label='Emergency Contact Number',
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter contact number', 'class': 'form-control'})
    )

    # ====================================================================
    # WHAT'S ADDED/MODIFIED: medical_conditions field definition
    # USE: Enforces max_length for optional text field.
    # ====================================================================
    medical_conditions = forms.CharField(
        label='Medical Conditions (Optional)',
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={'placeholder': 'Please list any medical conditions or allergies we should be aware of', 'class': 'form-control'})
    )
    # ====================================================================
    # WHAT'S ADDED/MODIFIED: fitness_goals field definition
    # USE: Enforces max_length for optional text field.
    # ====================================================================
    fitness_goals = forms.CharField(
        label='Fitness Goals (Optional)',
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={'placeholder': 'What are your fitness goals? This helps our staff provide better services', 'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = (
            'first_name', 'last_name', 'email', 'contact_number',
            'emergency_contact_name', 'emergency_contact_number',
            'medical_conditions', 'fitness_goals',
            'password', 'password_confirm'
        )
        widgets = {}
        help_texts = {
            'email': 'A valid email address is required for login.',
        }

    # ====================================================================
    # WHAT'S ADDED/MODIFIED: clean_first_name method
    # USE: Custom field-level validation for character restriction.
    # ====================================================================
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            # Regex: Allows letters (unicode), spaces, hyphens, and apostrophes
            if not regex.fullmatch(r"[\p{L} '\-]+", first_name):
                raise ValidationError("First name contains invalid characters. Only letters, spaces, hyphens, and apostrophes are allowed.")
        return first_name

    # ====================================================================
    # WHAT'S ADDED/MODIFIED: clean_last_name method
    # USE: Custom field-level validation for character restriction.
    # ====================================================================
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            # Regex: Allows letters (unicode), spaces, hyphens, and apostrophes
            if not regex.fullmatch(r"[\p{L} '\-]+", last_name):
                raise ValidationError("Last name contains invalid characters. Only letters, spaces, hyphens, and apostrophes are allowed.")
        return last_name

    # Email uniqueness validation remains the same
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    # ====================================================================
    # WHAT'S ADDED/MODIFIED: clean_contact_number method (refined)
    # USE: Strictly enforces 10 to 15 digit format.
    # ====================================================================
    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number')
        if contact_number:
            cleaned_digits = ''.join(filter(str.isdigit, contact_number))

            if not cleaned_digits:
                raise ValidationError("Please enter your contact number.")

            if len(cleaned_digits) < 10 or len(cleaned_digits) > 15:
                raise ValidationError("Contact number must be between 10 and 15 digits.")

            # Optional: Add specific country format regex if needed
            # if not regex.match(r"^((\+63)|0)\d{9,14}$", cleaned_digits):
            #     raise ValidationError("Please enter a valid Philippine contact number format.")

        return contact_number

    # ====================================================================
    # WHAT'S ADDED/MODIFIED: clean_emergency_contact_name method
    # USE: Custom field-level validation for character restriction.
    # ====================================================================
    def clean_emergency_contact_name(self):
        emergency_contact_name = self.cleaned_data.get('emergency_contact_name')
        if emergency_contact_name:
            # Regex: Allows letters (unicode) and spaces only
            if not regex.fullmatch(r"[\p{L} ]+", emergency_contact_name):
                raise ValidationError("Emergency contact name contains invalid characters. Only letters and spaces are allowed.")
        return emergency_contact_name

    # ====================================================================
    # WHAT'S ADDED/MODIFIED: clean_emergency_contact_number method (refined)
    # USE: Strictly enforces 10 to 15 digit format.
    # ====================================================================
    def clean_emergency_contact_number(self):
        emergency_contact_number = self.cleaned_data.get('emergency_contact_number')
        if emergency_contact_number:
            cleaned_digits = ''.join(filter(str.isdigit, emergency_contact_number))

            if not cleaned_digits:
                raise ValidationError("Please enter your emergency contact number.")

            if len(cleaned_digits) < 10 or len(cleaned_digits) > 15:
                raise ValidationError("Emergency contact number must be between 10 and 15 digits.")
        return emergency_contact_number

    # Form-level clean method (for password matching and password validators)
    def clean(self):
        super().clean()

        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if password and password_confirm is not None:
            if password != password_confirm:
                self.add_error('password_confirm', "Passwords do not match.")

        if password is not None and not self.errors.get('password'):
            try:
                validate_password(password, user=None)
            except ValidationError as e:
                self.add_error('password', e)

        return self.cleaned_data

    # Save method remains the same
    def save(self, commit=True):
        user = super().save(commit=False)
        if 'password' in self.cleaned_data:
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
