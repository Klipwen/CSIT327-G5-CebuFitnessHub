from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .forms import CustomUserRegistrationForm, MemberLoginForm
from .models import CustomUser, GymStaff


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
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately after successful registration
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Cebu Fitness Hub!')
            return redirect('member_dashboard') # Redirect to dashboard after login
        else:
            # If form is invalid, render the modal with errors
            return render(request, 'gymapp/register_modal.html', {'form': form})
    else:
        form = CustomUserRegistrationForm()
        
    return render(request, 'gymapp/register_modal.html', {'form': form})


def member_login(request):
    """
    Handle member login with email and password validation using the MemberLoginForm.
    Redirects to member_dashboard on success, or back to landing with an error message.
    """
    if request.method == 'POST':
        form = MemberLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            messages.success(request, 'Login Successful!')
            return redirect('member_dashboard') 
        else:
            messages.error(request, "Email or password is incorrect. Please try again.")
            return redirect('landing')
    return redirect('landing')


def staff_login(request):
    """
    Handle staff login with email and password validation.
    Authenticates against CustomUser (who has is_staff=True) or GymStaff if separate.
    Redirects to staff_dashboard on success, or back to landing with an error message.
    """
    # if request.method == 'POST':
    #     email = request.POST.get('email')
    #     password = request.POST.get('password')

    #     if email and password:
    #         user = authenticate(request, email=email, password=password)
    #         if user is not None and user.is_active and user.is_staff:
    #             login(request, user)
    #             messages.success(request, f'Welcome back, {user.first_name}!')
    #             return redirect('staff_dashboard')
    #         else:
    #             messages.error(request, 'Invalid email or password for staff account.')
    #     else:
    #         messages.error(request, 'Please fill in all fields.')
        
    #     return redirect('landing') # Redirect to landing to reopen modal and display error
    
    return redirect('landing') # For GET request, just redirect to landing


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