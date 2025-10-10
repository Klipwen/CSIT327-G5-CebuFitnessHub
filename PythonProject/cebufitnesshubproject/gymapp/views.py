from django.shortcuts import render
from django.shortcuts import render, redirect
from .forms import CustomUserRegistrationForm

#dashboard imports
from django.shortcuts import render
#from django.contrib.auth.decorators import login_required

#import the form from the forms.py file for registration
from .forms import CustomUserRegistrationForm #import the form


def landing_view(request):
	return render(request, 'gymapp/landing.html')

def register_member(request):
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save() # This creates a CustomUser and hashes the password!
            
            # Optional: Log the user in immediately after successful registration
            # login(request, user) 
            
            # Redirect to a success page or the landing page
            return redirect('member_dashboard')  # Consider creating a 'registration_success' page
        # If the form is NOT valid, it falls through to render the template with errors
    else: # This is a GET request, display an empty form
        form = CustomUserRegistrationForm()
        
    # Render the registration modal template, passing the form context
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