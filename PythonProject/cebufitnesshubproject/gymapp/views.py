import json
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .forms import (
    CustomUserRegistrationForm, FreezeRequestForm, MemberLoginForm, 
    PasswordChangeForm, UnfreezeRequestForm
)
# Corrected and expanded model imports
from .models import (
    CustomUser, GymStaff, gym_Member, Account_Request, 
    Billing_Record, Check_In, ClassSchedule, OCCUPANCY_TRACKER,
    Activity_Log, Notification
)
from django.views.decorators.http import require_http_methods
from django.db.models import Max, Sum, Count # For dashboard metrics
from django.db.models import F # For updating the tracker

# --- Landing, Registration, and Login/Logout (Unchanged) ---

def landing_view(request):
    open_login_modal = False
    if messages.get_messages(request): 
        open_login_modal = True
    if request.path == '/login/':
        open_login_modal = True
    
    context = {'open_login_modal': open_login_modal}
    return render(request, 'gymapp/landing.html', context)

def register_member(request):
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # The signal.py now handles profile creation automatically
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('landing') 
        else:
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
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if email and password:
            user = authenticate(request, email=email, password=password)
            if user is not None:
                if user.is_active:
                    # Enforce role chosen in the modal
                    role = request.POST.get('role', 'member')
                    if (role == 'staff' and not user.is_staff) or \
                       (role == 'member' and user.is_staff):
                        error_message = 'Invalid account.'
                        if is_ajax:
                            return JsonResponse({'success': False, 'error_type': 'role_mismatch', 'message': error_message})
                        else:
                            messages.error(request, error_message)
                            return redirect('landing')

                    login(request, user)
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    
                    redirect_url = 'staff_dashboard' if user.is_staff else 'member_dashboard'
                    
                    if is_ajax:
                        from django.urls import reverse
                        return JsonResponse({'success': True, 'redirect_url': reverse(redirect_url)})
                    else:
                        return redirect(redirect_url)
                else:
                    error_message = 'Your account is inactive.'
                    if is_ajax:
                        return JsonResponse({'success': False, 'error_type': 'email', 'message': error_message})
                    else:
                        messages.error(request, error_message)
                        return redirect('landing')
            else:
                # Provide error based on whether email or password was wrong
                try:
                    user_exists = CustomUser.objects.filter(email=email).exists()
                    error_type = 'password' if user_exists else 'email'
                    error_message = 'Invalid password.' if user_exists else 'Invalid account.'
                except:
                    error_type = 'general'
                    error_message = 'Invalid email or password.'
                
                if is_ajax:
                    return JsonResponse({'success': False, 'error_type': error_type, 'message': error_message})
                else:
                    messages.error(request, error_message)
                    return redirect('landing')
        else:
            missing_field = 'email' if not email else 'password'
            error_message = 'Please fill in all fields.'
            if is_ajax:
                return JsonResponse({'success': False, 'error_type': missing_field, 'message': error_message})
            else:
                messages.error(request, error_message)
                return redirect('landing')

    return redirect('landing')

def general_logout_view(request):
    """
    Handles logging out both members and staff by using Django's built-in logout.
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing')

# --- Member Dashboard Views (HEAVILY REVISED) ---

@login_required
def member_dashboard(request):
    """
    Renders the member dashboard with dynamic data.
    Now fetches data from the linked gym_Member profile.
    """
    if request.user.is_staff:
        messages.warning(request, 'Staff members should use the staff dashboard.')
        return redirect('staff_dashboard')
    
    try:
        # Fetch the member profile linked to the user
        member_profile = request.user.gym_member
    except gym_Member.DoesNotExist:
        messages.error(request, 'Member profile not found. Please contact support.')
        logout(request)
        return redirect('landing')

    # Get data from related models
    now = timezone.now()
    check_ins_this_month = Check_In.objects.filter(
        member=member_profile,
        check_in_time__month=now.month,
        check_in_time__year=now.year
    ).count()
    
    total_check_ins = Check_In.objects.filter(member=member_profile).count()
    
    # Get last 7 days of activity
    one_week_ago = now.date() - timezone.timedelta(days=7)
    weekly_activity = Activity_Log.objects.filter(
        member=member_profile,
        activity_date__gte=one_week_ago
    ).order_by('activity_date')

    context = {
        'user': request.user,
        'member_profile': member_profile,
        'days_attended_this_month': check_ins_this_month,
        'total_check_ins': total_check_ins,
        'weekly_activity': weekly_activity,
        'occupancy': OCCUPANCY_TRACKER.objects.first(), # Get the single occupancy record
    }
    return render(request, 'gymapp/dashboard.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def account_settings_view(request):
    """
    Handles displaying and processing all account settings forms:
    1. Password Change
    2. Freeze Request
    3. Unfreeze Request
    
    REWRITTEN to use gym_Member and Account_Request models.
    """
    user = request.user
    try:
        member_profile = user.gym_member
    except gym_Member.DoesNotExist:
        messages.error(request, 'Member profile not found.')
        return redirect('member_dashboard')

    modal_to_open = None
    
    # Check for an existing pending request
    pending_request = Account_Request.objects.filter(
        member=member_profile, 
        status='PENDING'
    ).first()

    # Initialize forms
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
                
                # Re-authenticate to keep the user logged in
                updated_user = authenticate(request, email=user.email, password=new_password)
                if updated_user:
                    login(request, updated_user)
                
                return redirect('account_settings')
            else:
                modal_to_open = 'password' # Re-open modal on error

        elif 'request_freeze' in request.POST:
            freeze_form = FreezeRequestForm(request.POST, prefix='freeze')
            if freeze_form.is_valid():
                if member_profile.is_frozen:
                    messages.info(request, 'Your account is already frozen.')
                elif pending_request:
                    messages.info(request, 'You already have a request pending review.')
                else:
                    # Create the Account_Request object
                    Account_Request.objects.create(
                        member=member_profile,
                        request_type='FREEZE',
                        reason=freeze_form.cleaned_data['reason'],
                        status='PENDING',
                        request_date=timezone.now()
                    )
                    messages.success(request, 'Freeze request submitted successfully.')
                return redirect('account_settings')
            else:
                modal_to_open = 'freeze' # Re-open modal on error

        elif 'request_unfreeze' in request.POST:
            unfreeze_form = UnfreezeRequestForm(request.POST, prefix='unfreeze')
            if unfreeze_form.is_valid():
                if not member_profile.is_frozen:
                     messages.info(request, 'Your account is already active.')
                elif pending_request:
                    messages.info(request, 'You already have a request pending review.')
                else:
                    # Create the Account_Request object
                    Account_Request.objects.create(
                        member=member_profile,
                        request_type='UNFREEZE',
                        reason=unfreeze_form.cleaned_data.get('reason', ''),
                        status='PENDING',
                        request_date=timezone.now()
                    )
                    messages.success(request, 'Unfreeze request submitted successfully.')
                return redirect('account_settings')
            else:
                modal_to_open = 'unfreeze' # Re-open modal on error

    context = {
        'user': user,
        'member_profile': member_profile,
        'password_form': password_form,
        'freeze_form': freeze_form,
        'unfreeze_form': unfreeze_form,
        'modal_to_open': modal_to_open,
        'pending_request': pending_request, # Pass pending request to template
        'is_frozen': member_profile.is_frozen, # Pass frozen status to template
    }
    return render(request, 'gymapp/account_settings.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def member_details_view(request):
    """
    Handles viewing and editing the user's *own* profile details.
    This view remains largely the same, as it edits CustomUser fields.
    """
    user: CustomUser = request.user 
    just_updated = False 

    if request.method == 'POST':
        # Update editable fields on the CustomUser model
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

@login_required
def check_in_view(request):
    """
    Fetches and displays the member's check-in history.
    """
    try:
        member_profile = request.user.gym_member
        check_in_history = Check_In.objects.filter(member=member_profile)
        
        # Calculate duration for each check-in
        history_with_duration = []
        for check_in in check_in_history:
            duration = None
            if check_in.check_out_time:
                time_diff = check_in.check_out_time - check_in.check_in_time
                duration = int(time_diff.total_seconds() / 60) # Duration in minutes
            history_with_duration.append({
                'check_in': check_in,
                'duration_minutes': duration
            })
            
        context = {'history': history_with_duration}
    except gym_Member.DoesNotExist:
        context = {'history': []}
        
    return render(request, 'gymapp/check_in.html', context)

@login_required
def billing_history_view(request):
    """
    Fetches and displays the member's billing history.
    """
    try:
        member_profile = request.user.gym_member
        billing_history = Billing_Record.objects.filter(member=member_profile)
        context = {
            'history': billing_history,
            'current_balance': member_profile.balance
        }
    except gym_Member.DoesNotExist:
        context = {'history': [], 'current_balance': 0}
        
    return render(request, 'gymapp/billing_history.html', context)

# --- Staff Dashboard Views (REVISED) ---
@login_required
def staff_dashboard_view(request):
    """
    Renders the staff dashboard with dynamic data.
    Now correctly fetches the linked staff profile.
    """
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('landing')

    try:
        # Fetch the staff profile
        staff_profile = request.user.gym_staff
    except GymStaff.DoesNotExist:
        messages.error(request, 'Staff profile not found. Please contact admin.')
        logout(request)
        return redirect('landing')

    # --- Data for Staff Overview (KPIs) ---
    now = timezone.now()
    pending_approvals = Account_Request.objects.filter(status='PENDING').count()

    # We get the list of members first
    active_members_list = gym_Member.objects.filter(user__is_active=True, is_frozen=False)

    # Then we get the count from that list
    active_members_count = active_members_list.count()

    todays_revenue = Billing_Record.objects.filter(
        transaction_type='PAYMENT',
        timestamp__date=now.date()
    ).aggregate(Sum('amount'))['amount__sum'] or 0.00

    monthly_revenue = Billing_Record.objects.filter(
        transaction_type='PAYMENT',
        timestamp__month=now.month,
        timestamp__year=now.year
    ).aggregate(Sum('amount'))['amount__sum'] or 0.00

    mrr = Billing_Record.objects.filter(
        transaction_type='FEE',
        timestamp__month=now.month,
        timestamp__year=now.year
    ).aggregate(Sum('amount'))['amount__sum'] or 0.00

    # --- NEW LOGIC BLOCK TO ADD ---
    # This processes the member list for the table
    member_data = []
    for member in active_members_list:
        # Find the LATEST check-in record for this member
        latest_checkin = member.check_ins.order_by('-check_in_time').first()

        is_checked_in = False
        last_checkin_time = None

        if latest_checkin:
            last_checkin_time = latest_checkin.check_in_time
            # Check if check_out_time is null (meaning they are still inside)
            if latest_checkin.check_out_time is None:
                is_checked_in = True

        member_data.append({
            'member': member,
            'is_checked_in': is_checked_in,  # True or False
            'last_checkin_time': last_checkin_time  # The full datetime object or None
        })
    # --- END OF NEW LOGIC BLOCK ---

    # Pass both the KPIs and the new member_list to the template
    context = {
        'staff_user': request.user,
        'staff_profile': staff_profile,
        'pending_approvals': pending_approvals,
        'active_members': active_members_count,  # For the KPI box
        'todays_revenue': todays_revenue,
        'monthly_revenue': monthly_revenue,
        'mrr': mrr,
        'notifications': Notification.objects.filter(recipient_staff=staff_profile, is_read=False),

        # --- NEW CONTEXT VARIABLE TO ADD ---
        'member_list': member_data,  # For the Member Management table
    }
    return render(request, 'gymapp/staff_dashboard.html', context)

@login_required
def class_schedule_view(request):
    """
    Fetches and displays the weekly class schedule.
    """
    # Fetch all class objects from the database
    # Order them by day and time, just like in the model's Meta
    schedule = ClassSchedule.objects.all().order_by('day_of_week', 'start_time')
    
    context = {
        'schedule': schedule
    }
    return render(request, 'gymapp/class_schedule.html', context)

@login_required
def check_in_out_view(request):
    """
    Handles the backend logic for a staff member manually
    checking a member in or out.
    """
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            member_id = data.get('member_id')
            action = data.get('action')
            
            member = get_object_or_404(gym_Member, user__pk=member_id)
            tracker = OCCUPANCY_TRACKER.objects.first()  # Get the tracker

            if action == 'checkin':
                # --- CHECK-IN LOGIC ---
                # 1. Create a new CheckIn record
                Check_In.objects.create(
                    member=member,
                    check_in_time=timezone.now(),
                    check_out_time=None  # This is important
                )
                
                # 2. Update the Occupancy Tracker
                if tracker:
                    tracker.current_count = F('current_count') + 1
                    tracker.last_updated = timezone.now()
                    tracker.save()
                
                return JsonResponse({'status': 'success', 'message': 'Member checked in.'})

            elif action == 'checkout':
                # --- CHECK-OUT LOGIC ---
                # 1. Find the latest check-in record that is still open
                latest_checkin = Check_In.objects.filter(
                    member=member,
                    check_out_time__isnull=True
                ).order_by('-check_in_time').first()
                
                if latest_checkin:
                    # 2. Close the record
                    latest_checkin.check_out_time = timezone.now()
                    latest_checkin.save()
                    
                    # 3. Update the Occupancy Tracker
                    if tracker and tracker.current_count > 0:
                        tracker.current_count = F('current_count') - 1
                        tracker.last_updated = timezone.now()
                        tracker.save()

                    # 4. (Optional but recommended) Create the Activity_Log record
                    duration = (latest_checkin.check_out_time - latest_checkin.check_in_time).total_seconds() / 60
                    Activity_Log.objects.create(
                        member=member,
                        activity_date=latest_checkin.check_in_time.date(),
                        duration_minutes=int(duration)
                    )
                    
                    return JsonResponse({'status': 'success', 'message': 'Member checked out.'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Could not find an open check-in record to close.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)



@login_required
@require_http_methods(["GET", "POST"]) # This view handles both
def staff_settings_view(request):
    """
    Handles loading and saving the global gym settings.
    """
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('landing')

    # Get the one and only settings object.
    # .get_or_create() ensures it exists on the first run.
    # We use 'pk=1' to always get the same row.
    settings, created = OCCUPANCY_TRACKER.objects.get_or_create(
        pk=1,
        defaults={
            'capacity_limit': 120,
            'peak_hours_start': '08:00',
            'peak_hours_end': '20:00',
            'default_monthly_fee': 2000.00,
            'gym_name': 'Cebu Fitness Hub',
            'contact_number': '+63 917 123 4567',
            'contact_address': '5th Floor, 8 Banawa Centrale, R. Duterte Street, Cebu City'
        }
    )

    # --- HANDLE POST REQUEST (from JavaScript fetch) ---
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Update all fields from the data sent by the JS
            settings.contact_number = data.get('contact_number')
            settings.default_monthly_fee = data.get('default_fee')
            settings.capacity_limit = data.get('gym_capacity')
            settings.peak_hours_start = data.get('peak_start')
            settings.peak_hours_end = data.get('peak_end')
            
            # You can also save gym_name and contact_address if you add them to your form
            
            settings.save()
            return JsonResponse({'status': 'success', 'message': 'Settings saved successfully!'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # --- HANDLE GET REQUEST (Normal page load) ---
    context = {
        'settings': settings,
        'staff_user': request.user # For the header/sidebar
    }
    return render(request, 'gymapp/staff_settings.html', context)

    
# --- Deprecated / Redundant Views ---
# The logic from these views has been consolidated into 'account_settings_view'
# and 'general_logout_view'. They can be safely removed from urls.py.

# def staff_logout_view(request):
#     ... (Redundant)

# def logout_confirm_view(request):
#     ... (Template can be used by general_logout_view if needed)

# def logout_prompt_view(request):
#     ... (Template can be used by general_logout_view if needed)

# def change_password(request):
#     ... (Logic moved to account_settings_view)

# def request_account_unfreeze(request):
#     ... (Logic moved to account_settings_view)

# def request_account_freeze(request):
#     ... (Logic moved to account_settings_view)