from django.shortcuts import render
from django.shortcuts import render, redirect
from .forms import RegistrationForm

#dashboard imports
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import MemberRegistration


def landing_view(request):
	return render(request, 'gymapp/landing.html')

def register_member(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()  # Save the form data to the database
            #return redirect('gymapp/landing.html')  # Redirect to a success page after submission
    else:
        form = RegistrationForm()
    return render(request, 'gymapp/register_modal.html', {'form': form})


#dashboard view
#@login_required
def member_dashboard(request):
    """
    Renders the member dashboard with dynamic and hardcoded data.
    """
    #try:
        # Assuming the logged-in user has a related MemberRegistration object.
        # This relationship may vary depending on your Django User model setup.
        # member = MemberRegistration.objects.get(email=request.user.email)
    #except MemberRegistration.DoesNotExist:
        # Handle case where no member registration is found for the user
        #member = None 

    # All hardcoded data as per the prompt
    context = {
        'member': 'John Doe',  # Placeholder name
        'account_balance': '₱2,040.00',  # Hardcoded value from the reference image
        'days_attended_this_month': 18,
        'total_checkins': 18,
        'next_payment_date': 'Jan 15, 2024',
        'weekly_activity': {
            'Mon': 75,
            'Tue': 90,
            'Wed': 60,
            'Thu': 105,
            'Fri': 85,
            'Sat': 120,
            'Sun': 0,
        },
        'gym_occupancy': {
            'status': 'Open',
            'peak_hours': '6:00–9:00 AM, 6:00–8:00 PM',
            'current': 67,
            'capacity': 120,
            'percentage': 56
        }
    }
    
    return render(request, 'gymapp/dashboard.html', context)