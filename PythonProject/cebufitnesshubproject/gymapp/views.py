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
    return render(request, 'gymapp/dashboard.html')


def staff_dashboard_view(request):
    """
    Test view to render the staff dashboard template with placeholder context.
    """
    context = {
        'staff_name': 'Test Staff',
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