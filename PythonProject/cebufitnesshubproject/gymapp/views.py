from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from .forms import CustomUserRegistrationForm
from .models import CustomUser, GymStaff


def landing_view(request):
	return render(request, 'gymapp/landing.html')

def register_member(request):
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save() # This creates a CustomUser and hashes the password!
            
            # Log the user in immediately after successful registration
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Cebu Fitness Hub!')
            
            # Redirect to member dashboard
            return redirect('member_dashboard')
        # If the form is NOT valid, it falls through to render the template with errors
    else: # This is a GET request, display an empty form
        form = CustomUserRegistrationForm()
        
    # Render the registration modal template, passing the form context
    return render(request, 'gymapp/register_modal.html', {'form': form})


def login_view(request):
    """
    Handle user login with automatic redirect based on user type.
    Support both regular form submission and AJAX requests.
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
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'error_type': 'email',
                            'message': 'Your account is inactive.'
                        })
                    else:
                        messages.error(request, 'Your account is inactive.')
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
    
    # For GET requests, just render the login page
    return render(request, 'gymapp/login.html')


#dashboard view
@login_required
def member_dashboard(request):
    """
    Renders the member dashboard with dynamic and hardcoded data.
    Only accessible to regular members (not staff).
    """
    # Additional check to ensure user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to access the member dashboard.')
        return redirect('landing')
    
    if request.user.is_staff:
        messages.warning(request, 'Staff members should use the staff dashboard.')
        return redirect('staff_dashboard')
    
    context = {
        'user': request.user,
        'member_name': request.user.get_full_name(),
    }
    return render(request, 'gymapp/dashboard.html', context)


def staff_dashboard_view(request):
    """
    Staff dashboard view - handles both login and dashboard display.
    """
    # Handle POST request (login attempt)
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email and password:
            try:
                # Find staff member by email
                staff = GymStaff.objects.get(email=email)
                
                # Check password using Django's password hasher
                if check_password(password, staff.password):
                    # Create a session for the staff member
                    request.session['staff_id'] = staff.staff_id
                    request.session['staff_email'] = staff.email
                    request.session['staff_name'] = staff.get_full_name()
                    
                    # Force session save
                    request.session.save()
                    
                    messages.success(request, f'Welcome back, {staff.first_name}!')
                    # Continue to show dashboard
                else:
                    messages.error(request, 'Invalid email or password.')
                    from django.http import HttpResponseRedirect
                    return HttpResponseRedirect('/')
            except GymStaff.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
                from django.http import HttpResponseRedirect
                return HttpResponseRedirect('/')
        else:
            messages.error(request, 'Please fill in all fields.')
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect('/')
    
    # Check if staff is logged in via session
    if 'staff_id' not in request.session:
        messages.error(request, 'Please log in to access the staff dashboard.')
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect('/')
    
    # Get staff information from session
    staff_id = request.session.get('staff_id')
    staff_name = request.session.get('staff_name', 'Staff Member')
    
    # Get additional staff information from database
    try:
        staff_record = GymStaff.objects.get(staff_id=staff_id)
        staff_email = staff_record.email
        staff_phone = staff_record.phone_number
    except GymStaff.DoesNotExist:
        messages.error(request, 'Staff record not found.')
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect('/')
    
    context = {
        'staff_id': staff_id,
        'staff_name': staff_name,
        'staff_email': staff_email,
        'staff_phone': staff_phone,
    }
    return render(request, 'gymapp/staff_dashboard.html', context)


def logout_confirm_view(request):
    """
    Simple page shown after confirming logout (no backend logic yet).
    """
    return render(request, 'gymapp/logout_confirm.html')


def logout_prompt_view(request):
    """
    Page that asks for logout confirmation (fallback when JS modal is not used).
    """
    return render(request, 'gymapp/logout_prompt.html')


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

