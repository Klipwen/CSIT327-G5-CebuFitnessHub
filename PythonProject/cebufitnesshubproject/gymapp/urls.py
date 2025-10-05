from django.urls import path
from .views import landing_view, register_member, member_dashboard, staff_dashboard_view, logout_confirm_view, logout_prompt_view

urlpatterns = [
    path('', landing_view, name='landing'),
    path('register/', register_member, name='register_submission'), # <-- This line is needed
    path('dashboard/', member_dashboard, name='member_dashboard'),#dashboard view
    path('staff_dashboard/', staff_dashboard_view, name='staff_dashboard'),
    path('logout/', logout_prompt_view, name='logout_prompt'),
    path('logout/confirm/', logout_confirm_view, name='logout_confirm'),
]
 