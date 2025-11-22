from django.db.models import Q # For complex 'OR' queries
from django.db.models.functions import TruncDay
from datetime import datetime, timedelta # Import timedelta and datetime utilities
from decimal import Decimal
from django.db import transaction
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
import calendar

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

            #first
            # --- START: NEW LOGIN LOGIC ---
            
            # First, try to find the user by their email.
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                user = None # User does not exist

            if user is not None:
                # User exists. NOW check their password and active status.
                if user.check_password(password):
                    # Password is correct.
                    if user.is_active:
                        # --- SUCCESS ---
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
                        
                        # Proceed with login
                        login(request, user)
                        messages.success(request, f'Welcome back, {user.first_name}!')
                        redirect_url = 'staff_dashboard' if user.is_staff else 'member_dashboard'
                        
                        if is_ajax:
                            from django.urls import reverse
                            return JsonResponse({'success': True, 'redirect_url': reverse(redirect_url)})
                        else:
                            return redirect(redirect_url)
                    
                    else:
                        # --- ERROR 1: ACCOUNT INACTIVE ---
                        # Password was correct, but is_active is False.
                        error_message = 'This account is inactive and awaiting staff activation.'
                        error_type = 'inactive'
                
                else:
                    # --- ERROR 2: INVALID PASSWORD ---
                    # User exists, but password was wrong.
                    error_message = 'Invalid password.'
                    error_type = 'password'
            
            else:
                # --- ERROR 3: USER DOES NOT EXIST ---
                error_message = 'Invalid account.'
                error_type = 'email'

            # --- This is the new, combined error handling ---
            if is_ajax:
                return JsonResponse({'success': False, 'error_type': error_type, 'message': error_message})
            else:
                messages.error(request, error_message)
                return redirect('landing')

            # --- END: NEW LOGIN LOGIC ---

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
#=========================================================================================================================================
#                                               NEW MEMBER_DASHBOARD VIEW
#=========================================================================================================================================
@login_required
def member_dashboard(request):
    """
    Renders the member dashboard with dynamic data.
    Now fetches data from the linked gym_Member profile.
    """
    # --- Access Control ---
    if request.user.is_staff:
        messages.warning(request, 'Staff members should use the staff dashboard.')
        return redirect('staff_dashboard')

    # --- Fetch Member Profile ---
    try:
        member_profile = request.user.gym_member
    except gym_Member.DoesNotExist:
        messages.error(request, 'Member profile not found. Please contact support.')
        logout(request)
        return redirect('landing')

    # --- Get Data from Related Models ---
    now = timezone.now()

    # NEW, CORRECTED CODE-----------------------------
    check_ins_this_month = Check_In.objects.filter(
        member=member_profile,
        check_in_time__month=now.month,
        check_in_time__year=now.year
    ).annotate(
        day=TruncDay('check_in_time')  # 1. Group check-ins by the calendar day
    ).values(
        'day'                         # 2. Get only the unique days
    ).distinct().count()              # 3. Count the unique days

    #-----------------------------------------------

    total_check_ins = Check_In.objects.filter(
        member=member_profile
    ).count()

    # Get last 7 days of activity logs
    one_week_ago = now.date() - timedelta(days=6)  # 6 days ago to include today (7 days total)
    weekly_activity_qs = Activity_Log.objects.filter(
        member=member_profile,
        activity_date__gte=one_week_ago
    )

    # --- Process Data for the Template ---

    # 1. Weekly Activity (convert queryset to dictionary)
    weekly_activity_dict = {
        'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0, 'Sat': 0, 'Sun': 0
    }
    day_map = {
        0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'
    }

    for log in weekly_activity_qs:
        day_name = day_map.get(log.activity_date.weekday())
        if day_name:
            weekly_activity_dict[day_name] += log.duration_minutes

    # 2. Account Status
    if member_profile.is_frozen:
        account_status = "Frozen"
    elif request.user.is_active:
        account_status = "Active"
    else:
        account_status = "Inactive"

    # 3. Occupancy Data
    occupancy = OCCUPANCY_TRACKER.objects.first()
    occupancy_percent = 0
    gym_status = "Open"

    if occupancy and occupancy.capacity_limit > 0:
        occupancy_percent = int((occupancy.current_count / occupancy.capacity_limit) * 100)

        # Determine gym status
        if occupancy_percent >= 95:
            gym_status = "Full"
        elif occupancy_percent >= 70:
            gym_status = "Peak"
        else:
            gym_status = "Open"

    # --- Final Context ---
    context = {
        'user': request.user,
        'member_profile': member_profile,
        'days_attended_this_month': check_ins_this_month,
        'total_check_ins': total_check_ins,
        'weekly_activity_dict': weekly_activity_dict,
        'account_status': account_status,
        'occupancy': occupancy,
        'occupancy_percent': occupancy_percent,
        'gym_status': gym_status,
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
    Fetches and displays the member's billing history,
    now with a calculated running balance for each transaction.
    """
    try:
        member_profile = request.user.gym_member
        
        # Get all transactions, newest first
        billing_history_qs = Billing_Record.objects.filter(member=member_profile).order_by('-timestamp')
        
        # --- THIS IS THE NEW LOGIC ---
        
        # Get the member's current balance (e.g., 1500)
        current_balance = member_profile.balance
        
        history_with_balance = []
        
        # Loop through the history (newest to oldest)
        for record in billing_history_qs:
            history_with_balance.append({
                'record': record,
                'balance_after_tx': current_balance
            })
            
            # "Rewind" the balance to what it was *before* this transaction
            # (Remember: Payments are negative, Fees are positive)
            current_balance = current_balance - record.amount 
            
        # --- END OF NEW LOGIC ---

        context = {
            'history': history_with_balance, # Pass the new processed list
            'current_balance': member_profile.balance # Keep passing this for the header (if needed)
        }
    except gym_Member.DoesNotExist:
        context = {'history': [], 'current_balance': 0}
        
    return render(request, 'gymapp/billing_history.html', context)

# --- Staff Dashboard Views (REVISED) ---
@login_required
def staff_dashboard_view(request):
    """
    Renders the staff dashboard with all dynamic data for KPIs,
    all member lists, approval queue, and notifications.
    """
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('landing')

    try:
        staff_profile = request.user.gym_staff
    except GymStaff.DoesNotExist:
        messages.error(request, 'Staff profile not found. Please contact admin.')
        logout(request)
        return redirect('landing')

    now = timezone.now()

    # --- 1. KPI DATA ---
    pending_approvals = Account_Request.objects.filter(status='PENDING').count()
    active_members_count = gym_Member.objects.filter(user__is_active=True, is_frozen=False).count()

    # We use .lstrip('-') to handle the negative 'PAYMENT' values
    todays_revenue = (Billing_Record.objects.filter(
        transaction_type='PAYMENT',
        timestamp__date=now.date()
    ).aggregate(Sum('amount'))['amount__sum'] or 0.00) * -1 # Multiply by -1 to make positive

    monthly_revenue = (Billing_Record.objects.filter(
        transaction_type='PAYMENT',
        timestamp__month=now.month,
        timestamp__year=now.year
    ).aggregate(Sum('amount'))['amount__sum'] or 0.00) * -1 # Multiply by -1
    
    # MRR (fees charged) are positive in your new 'Debt Ledger' model
    mrr = Billing_Record.objects.filter(
        transaction_type='FEE',
        timestamp__month=now.month,
        timestamp__year=now.year
    ).aggregate(Sum('amount'))['amount__sum'] or 0.00

    # --- 2. MEMBER MANAGEMENT TABLES ---

    search_query = request.GET.get('q', None) #new logic for search filter
    
    # Get the 3 separate member lists
    active_members_list = gym_Member.objects.filter(user__is_active=True, is_frozen=False).select_related('user')
    pending_members_list = gym_Member.objects.filter(user__is_active=False).select_related('user')
    frozen_members_list = gym_Member.objects.filter(is_frozen=True).select_related('user')

    # If a search query exists, filter the 'active' list
    if search_query:
        active_members_list = active_members_list.filter(
            Q(user__first_name__icontains=search_query) |  # Search by first name
            Q(user__last_name__icontains=search_query) |   # Search by last name
            Q(user__email__icontains=search_query) |      # Search by email
            Q(membership_id__icontains=search_query)    # Search by Member ID
        )
    # --- END OF SEARCH LOGIC ---

    # Process the 'Active' list (which you already did)
    active_member_data = []
    for member in active_members_list:
        latest_checkin = member.check_ins.order_by('-check_in_time').first()
        is_checked_in = False
        last_checkin_time = None
        if latest_checkin:
            last_checkin_time = latest_checkin.check_in_time
            if latest_checkin.check_out_time is None:
                is_checked_in = True
        active_member_data.append({
            'member': member,
            'is_checked_in': is_checked_in,
            'last_checkin_time': last_checkin_time
        })

    # Process the 'Frozen' list
    frozen_member_data = []
    for member in frozen_members_list:
        latest_checkin = member.check_ins.order_by('-check_in_time').first()
        frozen_member_data.append({
            'member': member,
            'last_checkin_time': latest_checkin.check_in_time if latest_checkin else None
        })
        
    # --- 3. APPROVAL QUEUE DATA ---
    approval_requests = Account_Request.objects.filter(status='PENDING').select_related('member__user')

    # --- 4. REVENUE TRACKER TABLE ---
    revenue_transactions = Billing_Record.objects.filter(
        transaction_type='PAYMENT'
    ).select_related('member__user').order_by('-timestamp')[:10] # Get last 10 payments

    # --- 5. NOTIFICATIONS ---
    # Get the 10 most recent notifications, regardless of read status
    notifications = Notification.objects.filter(
        recipient_staff=staff_profile
    ).order_by('-timestamp')[:10] # Get the 10 newest

    # --- 6. FINAL CONTEXT ---
    context = {
        'staff_user': request.user,
        'staff_profile': staff_profile,

        # --- ADD THIS LINE ---
        'settings': OCCUPANCY_TRACKER.objects.first(), # Pass settings to template
        # --- END ADD ---

        'search_query': search_query, # Pass the query back to the template
        
        # KPI Context
        'pending_approvals': pending_approvals,
        'active_members': active_members_count,
        'todays_revenue': todays_revenue,
        'monthly_revenue': monthly_revenue,
        'mrr': mrr,
        
        # Table Context
        'active_member_list': active_member_data,   # For 'Active' table
        'pending_member_list': pending_members_list, # For 'Pending' table
        'frozen_member_list': frozen_member_data,    # For 'Frozen' table
        'approval_requests': approval_requests,
        'revenue_transactions': revenue_transactions,
        'notifications': notifications,
    }
    return render(request, 'gymapp/staff_dashboard.html', context)

SCHEDULE_START_MINUTES = 7 * 60 + 30  # 7:30 AM
SCHEDULE_END_MINUTES = 19 * 60        # 7:00 PM
SCHEDULE_INTERVAL = 30

def _format_time_label(hour: int, minute: int) -> str:
    slot_dt = datetime(2000, 1, 1, hour, minute)
    return slot_dt.strftime('%I:%M %p').lstrip('0').replace(' 0', ' ')

def _build_time_slots():
    slots = []
    current = SCHEDULE_START_MINUTES
    while current < SCHEDULE_END_MINUTES:
        hour = current // 60
        minute = current % 60
        slots.append({
            'value': f'{hour:02d}:{minute:02d}',
            'label': _format_time_label(hour, minute)
        })
        current += SCHEDULE_INTERVAL
    return slots

DAY_COLUMNS = [
    {'label': 'Mon', 'full': 'Monday', 'value': 1},
    {'label': 'Tue', 'full': 'Tuesday', 'value': 2},
    {'label': 'Wed', 'full': 'Wednesday', 'value': 3},
    {'label': 'Thu', 'full': 'Thursday', 'value': 4},
    {'label': 'Fri', 'full': 'Friday', 'value': 5},
    {'label': 'Sat', 'full': 'Saturday', 'value': 6},
    {'label': 'Sun', 'full': 'Sunday', 'value': 7},
]

@login_required
def staff_schedule_view(request):
    """
    Renders the staff schedule management page.
    """
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('landing')

    context = {
        'day_columns': DAY_COLUMNS,
        'time_slots': _build_time_slots(),
        'schedule_start_minutes': SCHEDULE_START_MINUTES,
        'schedule_interval': SCHEDULE_INTERVAL,
    }
    return render(request, 'gymapp/staff_schedule.html', context)

def _parse_time_value(value):
    try:
        return datetime.strptime(value, '%H:%M').time()
    except (ValueError, TypeError):
        return None

def _time_to_minutes(time_value):
    return time_value.hour * 60 + time_value.minute

@login_required
@require_http_methods(["GET"])
def staff_schedule_data_view(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    classes = ClassSchedule.objects.all().order_by('day_of_week', 'start_time')
    payload = []
    for schedule in classes:
        payload.append({
            'class_id': schedule.class_id,
            'class_name': schedule.class_name,
            'instructor_name': schedule.instructor_name,
            'day_of_week': schedule.day_of_week,
            'day_label': schedule.get_day_of_week_display(),
            'start_time': schedule.start_time.strftime('%H:%M'),
            'end_time': schedule.end_time.strftime('%H:%M'),
            'start_label': schedule.start_time.strftime('%I:%M %p').lstrip('0'),
            'end_label': schedule.end_time.strftime('%I:%M %p').lstrip('0'),
        })

    return JsonResponse({'classes': payload})

@login_required
@require_http_methods(["POST"])
def staff_schedule_add_view(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, AttributeError):
        data = request.POST

    class_name = (data.get('class_name') or '').strip()
    instructor_name = (data.get('instructor_name') or '').strip()
    day_of_week = data.get('day_of_week')
    start_time_raw = data.get('start_time')
    end_time_raw = data.get('end_time')

    if not all([class_name, instructor_name, day_of_week, start_time_raw, end_time_raw]):
        return JsonResponse({'error': 'All fields are required.'}, status=400)

    try:
        day_of_week = int(day_of_week)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid day selected.'}, status=400)

    if day_of_week < 1 or day_of_week > 7:
        return JsonResponse({'error': 'Invalid day selected.'}, status=400)

    start_time = _parse_time_value(start_time_raw)
    end_time = _parse_time_value(end_time_raw)

    if not start_time or not end_time:
        return JsonResponse({'error': 'Invalid time format.'}, status=400)

    start_minutes = _time_to_minutes(start_time)
    end_minutes = _time_to_minutes(end_time)

    if end_minutes <= start_minutes:
        return JsonResponse({'error': 'End time must be later than start time.'}, status=400)

    if start_minutes < SCHEDULE_START_MINUTES or end_minutes > SCHEDULE_END_MINUTES:
        return JsonResponse({'error': 'Classes must be scheduled between 7:30 AM and 7:00 PM.'}, status=400)

    if ((start_minutes - SCHEDULE_START_MINUTES) % SCHEDULE_INTERVAL != 0 or
            (end_minutes - SCHEDULE_START_MINUTES) % SCHEDULE_INTERVAL != 0):
        return JsonResponse({'error': 'Times must be in 30-minute increments.'}, status=400)

    overlap_exists = ClassSchedule.objects.filter(
        day_of_week=day_of_week,
        start_time__lt=end_time,
        end_time__gt=start_time
    ).exists()

    if overlap_exists:
        return JsonResponse({'error': 'This time slot overlaps with an existing class.'}, status=400)

    new_class = ClassSchedule.objects.create(
        class_name=class_name,
        instructor_name=instructor_name,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        description=None,
        location=None,
    )

    return JsonResponse({
        'message': 'Class added successfully.',
        'class_id': new_class.class_id,
    }, status=201)

@login_required
@require_http_methods(["DELETE"])
def staff_schedule_delete_view(request, class_id):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    schedule_entry = get_object_or_404(ClassSchedule, pk=class_id)
    schedule_entry.delete()
    return JsonResponse({'message': 'Class deleted successfully.'})

# @login_required
# def member_schedule_view(request):
#     """
#     Renders the member schedule page (read-only view of weekly timetable).
#     """
#     if request.user.is_staff:
#         return redirect('staff_schedule')

#     context = {
#         'day_columns': DAY_COLUMNS,
#         'time_slots': _build_time_slots(),
#         'schedule_start_minutes': SCHEDULE_START_MINUTES,
#         'schedule_interval': SCHEDULE_INTERVAL,
#     }
#     return render(request, 'gymapp/member_schedule.html', context)

@login_required
def class_schedule_view(request):
    """
    Fetches and displays the weekly class schedule.
    DEPRECATED: Use member_schedule_view instead.
    """
    # Redirect to new member schedule view
    return redirect('member_schedule')

# @login_required
# def member_schedule_data_view(request):
#     # Members AND staff can use this
#     classes = ClassSchedule.objects.all().order_by('day_of_week', 'start_time')

#     payload = []
#     for schedule in classes:
#         payload.append({
#             'class_id': schedule.class_id,
#             'class_name': schedule.class_name,
#             'instructor_name': schedule.instructor_name,
#             'day_of_week': schedule.day_of_week,
#             'day_label': schedule.get_day_of_week_display(),
#             'start_time': schedule.start_time.strftime('%H:%M'),
#             'end_time': schedule.end_time.strftime('%H:%M'),
#             'start_label': schedule.start_time.strftime('%I:%M %p').lstrip('0'),
#             'end_label': schedule.end_time.strftime('%I:%M %p').lstrip('0'),
#         })

#     return JsonResponse({'classes': payload})


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


@login_required
def log_payment_view(request):
    """
    Handles the backend logic for a staff member logging a new payment.
    This is for *subsequent* payments, not initial activation.
    """
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            member_id = data.get('member_id')
            amount_str = data.get('amount')
            description = data.get('description', 'Onsite Payment')

            member = get_object_or_404(gym_Member, user__pk=member_id)
            amount = Decimal(amount_str)

            if amount <= 0:
                return JsonResponse({'status': 'error', 'message': 'Amount must be positive.'})

            # Prevent logging payments when there is no outstanding balance
            if member.balance <= 0:
                return JsonResponse({'status': 'error', 'message': 'Member has no outstanding balance.'})

            with transaction.atomic():
                # 1. Update the member's balance (they owe less money)
                member.balance = F('balance') - amount
                member.save()

                # 2. Create the Billing_Record (no 'new_balance' field)
                Billing_Record.objects.create(
                    member=member,
                    staff_processor=request.user.gym_staff,
                    transaction_type='PAYMENT',
                    amount = -amount, # Payments are negative
                    description=description
                )

            return JsonResponse({'status': 'success', 'message': 'Payment logged.'})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


@login_required
def manual_freeze_view(request):
    """
    Handles the backend logic for a staff member manually
    freezing an active account and pausing their plan.
    """
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            member_id = data.get('member_id')
            reason = data.get('reason', 'Manually frozen by staff.')
            member = get_object_or_404(gym_Member, user__pk=member_id)

            if member.is_frozen:
                return JsonResponse({'status': 'error', 'message': 'Account is already frozen.'})

            with transaction.atomic():
                # --- YOUR NEW LOGIC ---
                days_remaining = 0
                if member.next_due_date:
                    days_remaining = (member.next_due_date - timezone.now().date()).days
                
                # 1. Update the member's status
                member.is_frozen = True
                member.days_remaining_on_freeze = days_remaining if days_remaining > 0 else 0
                member.next_due_date = None # Pause the due date
                member.save()
                
                # 2. Create an Account_Request for auditing
                Account_Request.objects.create(
                    member=member,
                    staff_reviewer=request.user.gym_staff,
                    request_type='FREEZE',
                    reason=reason,
                    status='APPROVED',
                    staff_decision_reason='Manually applied by staff.',
                    decision_date=timezone.now()
                )
            
            return JsonResponse({'status': 'success', 'message': 'Account frozen.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

@login_required
def process_request_view(request):
    """
    Handles the backend logic for approving or rejecting
    a member's Freeze/Unfreeze request.
    """
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            request_id = data.get('request_id')
            action = data.get('action') # 'approve' or 'reject'
            staff_reason = data.get('staff_reason', '')

            req = get_object_or_404(Account_Request, request_id=request_id, status='PENDING')
            member = req.member

            with transaction.atomic():
                if action == 'approve':
                    req.status = 'APPROVED'
                    # Update the member's 'is_frozen' status
                    if req.request_type == 'FREEZE':
                        member.is_frozen = True
                    elif req.request_type == 'UNFREEZE':
                        member.is_frozen = False
                
                elif action == 'reject':
                    req.status = 'REJECTED'
                    req.staff_decision_reason = staff_reason
                
                req.staff_reviewer = request.user.gym_staff
                req.decision_date = timezone.now()
                
                req.save()
                member.save()
            
            return JsonResponse({'status': 'success', 'message': f'Request {action}d.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


@login_required
def activate_member_view(request):
    """
    Handles the backend logic for activating a new member
    and processing their first payment.
    """
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            member_id = data.get('member_id')
            amount_str = data.get('amount')
            description = data.get('description', 'Initial Activation Payment')

            member = get_object_or_404(gym_Member, user__pk=member_id)
            if member.user.is_active:
                return JsonResponse({'status': 'error', 'message': 'Member is already active.'})
                
            amount_paid = Decimal(amount_str)
            
            # Get the single source of truth for the fee
            settings = OCCUPANCY_TRACKER.objects.get(pk=1)
            default_fee = settings.default_monthly_fee

            # --- 1. MEMBERSHIP ID GENERATOR LOGIC ---
            current_year = timezone.now().year
            prefix = settings.member_id_prefix or "CFH"

            # Count members from this year to get the next sequential number
            members_this_year = gym_Member.objects.filter(
                membership_id__startswith=f"{prefix}-{current_year}-"
            ).count()
            
            next_seq_number = members_this_year + 1
            
            # Format the ID: CFH-2025-0009
            new_membership_id = f"{prefix}-{current_year}-{next_seq_number:04d}"
            # --- END OF ID GENERATOR ---

            #-----------------------------------------------------------------------

            with transaction.atomic():
                # 1. Calculate the new balance based on your logic
                # (Balance = Fee - Downpayment)
                new_balance = default_fee - amount_paid
                
                # 2. Update the Member's profile
                member.balance = new_balance
                member.is_frozen = False
                member.next_due_date = timezone.now().date() + timedelta(days=30)
                member.membership_id = new_membership_id # <-- SAVE THE NEW ID FOR ID GENERATOR
                member.save()
                
                # 3. Update the base CustomUser
                member.user.is_active = True 
                member.user.save()

                # 4. Create the FEE record
                Billing_Record.objects.create(
                    member=member,
                    staff_processor=request.user.gym_staff,
                    transaction_type='FEE',
                    amount=default_fee, # Positive amount to create debt
                    description="Initial Membership Fee"
                )
                
                # 5. Create the PAYMENT record
                Billing_Record.objects.create(
                    member=member,
                    staff_processor=request.user.gym_staff,
                    transaction_type='PAYMENT',
                    amount = -amount_paid, # Negative amount to clear debt
                    description=description
                )
            
            return JsonResponse({'status': 'success', 'message': 'Member activated successfully.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405) 

@login_required
def manual_unfreeze_view(request):
    """
    Handles the backend logic for a staff member manually
    unfreezing an account and resuming their plan.
    """
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            member_id = data.get('member_id')
            reason = data.get('reason', 'Manually unfrozen by staff.')
            member = get_object_or_404(gym_Member, user__pk=member_id)

            if not member.is_frozen:
                return JsonResponse({'status': 'error', 'message': 'Account is already active.'})

            with transaction.atomic():
                # --- YOUR NEW LOGIC ---
                days_remaining = member.days_remaining_on_freeze or 0
                new_due_date = timezone.now().date() + timedelta(days=days_remaining)
                
                # 1. Update the member's status
                member.is_frozen = False
                member.days_remaining_on_freeze = None # Clear the saved days
                member.next_due_date = new_due_date # Set new expiry date
                member.save()
                
                # 2. Create an Account_Request for auditing
                Account_Request.objects.create(
                    member=member,
                    staff_reviewer=request.user.gym_staff,
                    request_type='UNFREEZE',
                    reason=reason,
                    status='APPROVED',
                    staff_decision_reason='Manually applied by staff.',
                    decision_date=timezone.now()
                )
            
            return JsonResponse({'status': 'success', 'message': 'Account unfrozen.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405) 


@login_required
def edit_member_view(request):
    """
    Handles a staff member editing a member's profile details.
    """
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            member_id = data.get('member_id')

            # We get the CustomUser object, not the profile,
            # because all these fields are on the CustomUser.
            user_to_edit = get_object_or_404(CustomUser, pk=member_id)

            # Update all the editable fields
            user_to_edit.first_name = data.get('first_name', user_to_edit.first_name)
            user_to_edit.last_name = data.get('last_name', user_to_edit.last_name)
            user_to_edit.contact_number = data.get('contact_number', user_to_edit.contact_number)
            user_to_edit.emergency_contact_name = data.get('emergency_contact_name', user_to_edit.emergency_contact_name)
            user_to_edit.emergency_contact_number = data.get('emergency_contact_number', user_to_edit.emergency_contact_number)
            user_to_edit.medical_conditions = data.get('medical_conditions', user_to_edit.medical_conditions)
            user_to_edit.fitness_goals = data.get('fitness_goals', user_to_edit.fitness_goals)
            
            user_to_edit.save()
            
            return JsonResponse({'status': 'success', 'message': 'Member details updated.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


# -----------------------------------------------------------------
# --- Imlementing Chart in Staff dashboard ---
# -----------------------------------------------------------------
@login_required
def revenue_chart_data_view(request):
    """
    API endpoint to send revenue data for the chart.
    Handles two filter types:
    - 'daily': Returns daily totals for the current month.
    - 'monthly': Returns monthly totals for the current year.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    filter_type = request.GET.get('filter', 'daily') # Default to 'daily'
    now = timezone.now()
    
    # We only care about payments (negative numbers in the 'Debt Ledger')
    base_queryset = Billing_Record.objects.filter(transaction_type='PAYMENT')

    if filter_type == 'monthly':
        # --- LOGIC FOR "THIS YEAR (MONTHLY)" ---
        
        # 1. Get all payments for the current year
        payments_this_year = base_queryset.filter(timestamp__year=now.year)
        
        # 2. Format for Chart.js
        labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        data = [0.0] * 12 # A list of 12 zeros
        
        for payment in payments_this_year:
            # (payment.amount is negative, so *-1 makes it positive)
            data[payment.timestamp.month - 1] += float(payment.amount * -1)

    else:
        # --- LOGIC FOR "THIS MONTH (DAILY)" ---
        
        # 1. Get all payments for the current month and year
        payments_this_month = base_queryset.filter(
            timestamp__year=now.year,
            timestamp__month=now.month
        )
        
        # 2. Format for Chart.js
        num_days = calendar.monthrange(now.year, now.month)[1] # Gets days in current month (e.g., 30)
        labels = [f"{now.strftime('%b')} {day}" for day in range(1, num_days + 1)] # e.g., ["Nov 1", "Nov 2", ...]
        data = [0.0] * num_days # A list of 30 zeros

        for payment in payments_this_month:
            # (payment.amount is negative, so *-1 makes it positive)
            data[payment.timestamp.day - 1] += float(payment.amount * -1)

    return JsonResponse({
        'labels': labels,
        'data': data
    })


@login_required
def mark_notification_read_view(request, notification_id):
    """
    Marks a specific notification as 'read' and redirects
    the staff member to the appropriate page.
    """
    if not request.user.is_staff:
        return redirect('landing')
    
    # Find the notification, making sure it belongs to the logged-in staff
    notification = get_object_or_404(
        Notification, 
        notification_id=notification_id, 
        recipient_staff=request.user.gym_staff
    )
    
    # Mark it as read
    if not notification.is_read:
        notification.is_read = True
        notification.save()
        
    # Redirect to the URL stored on the notification
    if notification.redirect_url:
        return redirect(notification.redirect_url)
    
    # Fallback if no URL is set
    return redirect('staff_dashboard')

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