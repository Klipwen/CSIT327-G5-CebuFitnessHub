from django.urls import path
from .views import (
    landing_view,
    register_member,
    member_login,
    member_dashboard,
    account_settings_view,
    staff_dashboard_view,
    
    # This new view handles all logout logic
    general_logout_view, 

    # --- These views are no longer needed ---
    # The logic for change_password, request_account_unfreeze, 
    # and request_account_freeze is now handled inside 'account_settings_view'.
    
    # logout_confirm_view,
    # logout_prompt_view,
    # staff_logout_view,
    # change_password,
    # request_account_unfreeze,
    # request_account_freeze,
    
    member_details_view,
    check_in_view,
    billing_history_view,
    
    # We must add the new ClassSchedule view
    class_schedule_view, 
    check_in_out_view,
    staff_settings_view,
    log_payment_view,
    manual_freeze_view,
    process_request_view,
    activate_member_view,
    manual_unfreeze_view,
    edit_member_view,
    revenue_chart_data_view,
    mark_notification_read_view,
    fetch_notifications_api, #for auto refresh(asks the server, "Any new notifications?" every 5 seconds)
)

urlpatterns = [
    path('', landing_view, name='landing'),
    path('register/', register_member, name='register_submission'),
    path('login/', member_login, name='member_login'),
    
    # This is the new, correct path for logging out
    path('logout/', general_logout_view, name='logout'), 

    path('dashboard/', member_dashboard, name='member_dashboard'),
    path('account/settings/', account_settings_view, name='account_settings'),
    path('member_details/', member_details_view, name='member_details'),
    path('check_in/', check_in_view, name='check_in'),
    path('billing_history/', billing_history_view, name='billing_history'),
    
    # Add the path for the new Class Schedule feature
    path('class_schedule/', class_schedule_view, name='class_schedule'),

    path('staff_dashboard/', staff_dashboard_view, name='staff_dashboard'),

    path('staff/check-in-out/', check_in_out_view, name='check_in_out_view'),
    path('staff/settings/', staff_settings_view, name='staff_settings'),
    path('staff/log-payment/', log_payment_view, name='log_payment_view'),
    path('staff/manual-freeze/', manual_freeze_view, name='manual_freeze_view'),
    path('staff/process-request/', process_request_view, name='process_request_view'),
    path('staff/activate-member/', activate_member_view, name='activate_member_view'),
    path('staff/manual-unfreeze/', manual_unfreeze_view, name='manual_unfreeze_view'),
    path('staff/edit-member/', edit_member_view, name='edit_member_view'),
    path('staff/revenue-chart-data/', revenue_chart_data_view, name='revenue_chart_data'),
    path('staff/notifications/read/<int:notification_id>/', mark_notification_read_view, name='mark_notification_read'),
    path('staff/api/notifications/', fetch_notifications_api, name='fetch_notifications_api'),
    
    # --- These paths are no longer needed ---
    # They all point to views that have been consolidated.
    
    # path('logout/', logout_prompt_view, name='logout_prompt'),
    # path('staff-logout/', staff_logout_view, name'staff_logout'),
    # path('logout/confirm/', logout_confirm_view, name='logout_confirm'),  
    # path('account/change-password/', change_password, name='change_password'),
    # path('account/request-unfreeze/', request_account_unfreeze, name='request_account_unfreeze'),
    # path('account/request-freeze/', request_account_freeze, name='request_account_freeze'),
]