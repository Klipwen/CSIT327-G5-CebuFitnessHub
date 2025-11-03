from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse # Kept from feat/staff-login-validation
from .forms import CustomUserRegistrationForm, FreezeRequestForm, MemberLoginForm, PasswordChangeForm, UnfreezeRequestForm # Kept both forms from both branches
from .models import CustomUser, GymStaff
from django.views.decorators.http import require_http_methods


def landing_view(request):
    open_login_modal = False
    
    # Check if there are messages (from a redirect, e.g., failed login, successful registration)
    # This ensures the modal opens to show the message.
    if messages.get_messages(request): 
        open_login_modal = True
    
    # If the URL path is '/login/', explicitly open the login modal
    if request.path == '/login/':
        open_login_modal = True

    context = {
        'open_login_modal': open_login_modal,
    }
    return render(request, 'gymapp/landing.html', context)


def register_member(request):
    just_updated = False
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately after successful registration commented out for now
            #login(request, user)
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('landing') # Redirect to landing page after registration
        else:
            # If form is invalid, render the modal with errors
            return render(request, 'gymapp/register_modal.html', {'form': form})
    else:
        form = CustomUserRegistrationForm()
        
    return render(request, 'gymapp/register_modal.html', {'form': form})


def member_login(request):
    """
    Handle user login with automatic redirect based on user type.
    Support both regular form submission and AJAX requests.
    This view now handles both member and staff logins.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if email and password:
            user = authenticate(request, email=email, password=password)
            if user is not None:
                if user.is_active:
                    # Enforce role chosen in the modal
                    role = request.POST.get('role', 'member')
                    if role == 'staff' and not user.is_staff:
                        error_message = 'Invalid account.'
                        if is_ajax:
                            return JsonResponse({
                                'success': False,
                                'error_type': 'role_mismatch',
                                'message': error_message
                            })
                        else:
                            messages.error(request, error_message)
                            return redirect('landing')
                    if role == 'member' and user.is_staff:
                        error_message = 'Invalid account.'
                        if is_ajax:
                            return JsonResponse({
                                'success': False,
                                'error_type': 'role_mismatch',
                                'message': error_message
                            })
                        else:
                            messages.error(request, error_message)
                            return redirect('landing')

                    # Proceed with login since role matches
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    
                    # Determine redirect URL based on user type
                    redirect_url = 'staff_dashboard' if user.is_staff else 'member_dashboard'
                    
                    if is_ajax:
                        from django.urls import reverse
                        return JsonResponse({
                            'success': True,
                            'redirect_url': reverse(redirect_url)
                        })
                    else:
                        return redirect(redirect_url)
                else:
                    error_message = 'Your account is inactive.'
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'error_type': 'email',
                            'message': error_message
                        })
                    else:
                        messages.error(request, error_message)
            else:
                # Try to determine if the email exists to provide more specific error
                try:
                    user_exists = CustomUser.objects.filter(email=email).exists()
                    if user_exists:
                        error_type = 'password'
                        error_message = 'Invalid password.'
                    else:
                        error_type = 'email'
                        error_message = 'Invalid account.'
                except:
                    error_type = 'general'
                    error_message = 'Invalid email or password.'
                
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error_type': error_type,
                        'message': error_message
                    })
                else:
                    messages.error(request, error_message)
        else:
            missing_field = 'email' if not email else 'password'
            error_message = 'Please fill in all fields.'
            
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error_type': missing_field,
                    'message': error_message
                })
            else:
                messages.error(request, error_message)
    
    # For GET requests, just render the login page, or redirect to landing if this view is mapped to a path that's not meant to be accessed via GET directly.
    # Assuming this view is only posted to via AJAX or a form, redirect to landing for safety on GET.
    return redirect('landing')


@login_required
def member_dashboard(request):
    """
    Renders the member dashboard with dynamic data.
    Only accessible to regular members (not staff) who are logged in.
    """
    if not request.user.is_authenticated: # Redundant with @login_required but kept for clarity
        messages.error(request, 'Please log in to access the member dashboard.')
        return redirect('landing')
    
    if request.user.is_staff:
        messages.warning(request, 'Staff members should use the staff dashboard.')
        return redirect('staff_dashboard')
    
    context = {
        'user': request.user,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'email': request.user.email,
        'date_joined': request.user.date_joined.strftime('%m/%d/%Y'),
        'member_name': request.user.get_full_name(), 
    }
    return render(request, 'gymapp/dashboard.html', context)


@login_required
def account_settings_view(request):
    """
    Handles both displaying the settings page (GET) and processing all
    form submissions (POST) for this page.
    """
    user = request.user
    
    # This variable will hold the name of the modal to open on page load, if any.
    modal_to_open = None
    
    # Initialize forms with unique prefixes for the GET request
    password_form = PasswordChangeForm(request=request, prefix='pw')
    freeze_form = FreezeRequestForm(prefix='freeze')
    unfreeze_form = UnfreezeRequestForm(prefix='unfreeze')

    if request.method == 'POST':
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.POST, request=request, prefix='pw')
            if password_form.is_valid():
                new_password = password_form.cleaned_data['new_password']
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password changed successfully.')
                
                updated_user = authenticate(request, email=user.email, password=new_password)
                if updated_user:
                    login(request, updated_user)
                
                return redirect('account_settings')
            else:
                # If form is invalid, set the flag and prepare to re-render
                modal_to_open = 'password'
                #messages.error(request, 'Please fix the password errors below.')

        elif 'request_freeze' in request.POST:
            freeze_form = FreezeRequestForm(request.POST, prefix='freeze')
            if freeze_form.is_valid():
                if user.freeze_request_status == 'pending':
                    messages.info(request, 'Freeze request is already pending.')
                else:
                    user.freeze_request_status = 'pending'
                    user.freeze_requested_at = timezone.now()
                    user.save()
                    messages.success(request, 'Freeze request submitted successfully.')
                return redirect('account_settings')
            else:
                # If form is invalid, set the flag and prepare to re-render
                modal_to_open = 'freeze'
                messages.error(request, 'Please provide a valid reason for the freeze request.')

        elif 'request_unfreeze' in request.POST:
            unfreeze_form = UnfreezeRequestForm(request.POST, prefix='unfreeze')
            if unfreeze_form.is_valid():
                if user.unfreeze_request_status == 'pending':
                    messages.info(request, 'Unfreeze request is already pending.')
                else:
                    user.unfreeze_request_status = 'pending'
                    user.unfreeze_requested_at = timezone.now()
                    user.save()
                    messages.success(request, 'Unfreeze request submitted successfully.')
                return redirect('account_settings')
            else:
                # If form is invalid, set the flag and prepare to re-render
                modal_to_open = 'unfreeze'
                messages.error(request, 'There was an error with your unfreeze request.')

    # ====================================================================
    # This context is used for BOTH the initial GET request AND for re-rendering
    # the page when a POST request fails validation. It correctly includes
    # the form instances (which will contain errors if validation failed).
    # ====================================================================
    context = {
        'member_name': user.get_full_name(),
        'password_form': password_form,
        'freeze_form': freeze_form,
        'unfreeze_form': unfreeze_form,
        'modal_to_open': modal_to_open, # This single variable controls which modal opens
    }
    return render(request, 'gymapp/account_settings.html', context)


@login_required
def staff_dashboard_view(request):
    """
    Renders the staff dashboard with dynamic data.
    Only accessible to staff members who are logged in via Django's auth.
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, 'You do not have permission to access the staff dashboard.')
        return redirect('landing')

    # Assuming CustomUser has relevant staff attributes or can be linked to GymStaff
    # If GymStaff is a separate model with additional fields, fetch them.
    staff_record = None
    try:
        staff_record = GymStaff.objects.get(custom_user=request.user) # Assuming a one-to-one link
    except GymStaff.DoesNotExist:
        # Handle cases where a staff CustomUser doesn't have a linked GymStaff profile
        # Or if GymStaff model is deprecated/not used for direct login.
        pass

    context = {
        'staff_id': request.user.id, 
        'staff_name': request.user.get_full_name(),
        'staff_email': request.user.email,
        'staff_phone': staff_record.phone_number if staff_record else 'N/A', # Example
        # Add other staff-specific data from CustomUser or GymStaff
    }
    return render(request, 'gymapp/staff_dashboard.html', context)

def staff_logout_view(request):
    """
    Handle staff logout by clearing session data.
    """
    # Clear staff session data
    if 'staff_id' in request.session:
        del request.session['staff_id']
    if 'staff_email' in request.session:
        del request.session['staff_email']
    if 'staff_name' in request.session:
        del request.session['staff_name']
    
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing')

def logout_confirm_view(request):
    return render(request, 'gymapp/logout_confirm.html')


def logout_prompt_view(request):
    return render(request, 'gymapp/logout_prompt.html')


def general_logout_view(request):
    """
    Handles logging out both members and staff by using Django's built-in logout.
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing')


@login_required
def change_password(request):
    """Handle member password change."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            current_password = form.cleaned_data['current_password']
            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
                return redirect('account_settings')

            new_password = form.cleaned_data['new_password']
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Password changed successfully.')
            # Re-authenticate after password change
            user = authenticate(request, email=request.user.email, password=new_password)
            if user:
                login(request, user)
            return redirect('account_settings')
        else:
            #messages.error(request, 'Please fix the errors in the form.')
            return redirect('account_settings')
    return redirect('account_settings')


@login_required
def request_account_unfreeze(request):
    """Allow a member to request account unfreeze."""
    if request.method == 'POST':
        user = request.user
        # Only allow one pending request
        if user.unfreeze_request_status == 'pending':
            messages.info(request, 'Unfreeze request is already pending.')
            return redirect('account_settings')

        from django.utils import timezone
        user.unfreeze_request_status = 'pending'
        user.unfreeze_requested_at = timezone.now()
        user.save()
        messages.success(request, 'Unfreeze request submitted. We will review it shortly.')
        return redirect('account_settings')
    return redirect('account_settings')


@login_required
def request_account_freeze(request):
    """Allow a member to request account freeze."""
    if request.method == 'POST':
        user = request.user
        # Only allow one pending request
        if user.freeze_request_status == 'pending':
            messages.info(request, 'Freeze request is already pending.')
            return redirect('account_settings')

        from django.utils import timezone
        user.freeze_request_status = 'pending'
        user.freeze_requested_at = timezone.now()
        user.save()
        messages.success(request, 'Freeze request submitted. We will review it shortly.')
        return redirect('account_settings')
    return redirect('account_settings')

@login_required
@require_http_methods(["GET", "POST"])
def member_details_view(request):
    user: CustomUser = request.user  
    just_updated = False  

    if request.method == 'POST':
        # Update only editable fields
        user.contact_number = request.POST.get('contact_number', user.contact_number)
        user.fitness_goals = request.POST.get('fitness_goals', user.fitness_goals)
        user.emergency_contact_name = request.POST.get('emergency_contact_name', user.emergency_contact_name)
        user.emergency_contact_number = request.POST.get('emergency_contact_number', user.emergency_contact_number)

        user.save()
        messages.success(request, 'Details updated successfully!')
        just_updated = True  

    context = {
        'user': user,
        'full_name': user.get_full_name(),
        'email': user.email,
        'contact_number': user.contact_number or '',
        'fitness_goals': user.fitness_goals or '',
        'emergency_contact_name': user.emergency_contact_name or '',
        'emergency_contact_number': user.emergency_contact_number or '',
        'date_joined': user.date_joined,
        'just_updated': just_updated, 
    }
    return render(request, 'gymapp/member_details.html', context)

# Check-in History
@login_required
def check_in_view(request):
    return render(request, 'gymapp/check_in.html')

# Billing History
@login_required
def billing_history_view(request):
    return render(request, 'gymapp/billing_history.html')