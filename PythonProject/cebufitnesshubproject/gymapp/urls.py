from django.urls import path
from .views import (
    landing_view,
    register_member,
    member_login,
    member_dashboard,
    account_settings_view,
    staff_dashboard_view,
    logout_confirm_view,
    logout_prompt_view,
    staff_logout_view,
    change_password,
    request_account_unfreeze,
    request_account_freeze,
)

urlpatterns = [
    path('', landing_view, name='landing'),
    path('register/', register_member, name='register_submission'),
    path('login/', member_login, name='member_login'),
    path('dashboard/', member_dashboard, name='member_dashboard'),
    path('account/settings/', account_settings_view, name='account_settings'),
    path('staff_dashboard/', staff_dashboard_view, name='staff_dashboard'),
    path('logout/', logout_prompt_view, name='logout_prompt'),
    path('staff-logout/', staff_logout_view, name='staff_logout'),
    path('logout/confirm/', logout_confirm_view, name='logout_confirm'),
    path('account/change-password/', change_password, name='change_password'),
    path('account/request-unfreeze/', request_account_unfreeze, name='request_account_unfreeze'),
    path('account/request-freeze/', request_account_freeze, name='request_account_freeze'),
]
 