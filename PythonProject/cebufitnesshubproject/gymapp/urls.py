from django.urls import path
from .views import landing_view, register_member, member_dashboard # <-- You need to import register_member

urlpatterns = [
    path('', landing_view, name='landing'),
    path('register/', register_member, name='register_submission'), # <-- This line is needed
    path('dashboard/', member_dashboard, name='member_dashboard'),#dashboard view
]
 