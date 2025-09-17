# trainer_management/urls.py - Updated with edit trainer

from django.urls import path
from . import views

app_name = 'trainer_management'

urlpatterns = [
    # Trainer Management (for Gym Admins)
    path('gym/<int:gym_id>/trainers/', views.trainer_list, name='trainer_list'),
    path('gym/<int:gym_id>/trainers/add/', views.add_trainer, name='add_trainer'),
    path('gym/<int:gym_id>/trainers/<int:trainer_id>/', views.trainer_detail, name='trainer_detail'),
    
    # NEW: Edit trainer URL - ADD THIS LINE
    path('gym/<int:gym_id>/trainers/<int:trainer_id>/edit/', views.edit_trainer, name='edit_trainer'),
    
    path('gym/<int:gym_id>/trainers/<int:trainer_id>/assign-members/', views.assign_members_to_trainer, name='assign_members'),
    path('gym/<int:gym_id>/trainers/<int:trainer_id>/permissions/', views.trainer_permissions, name='trainer_permissions'),
    
    # Trainer Dashboard
    path('dashboard/', views.trainer_dashboard, name='trainer_dashboard'),
    
    # Session Management
    path('sessions/', views.session_list, name='session_list'),
    path('member-list/', views.trainer_member_list, name='trainer_member_list'),
    path('sessions/create/', views.create_session, name='create_session'),
    path('sessions/<int:session_id>/', views.session_detail, name='session_detail'),
    path('sessions/<int:session_id>/add-content/', views.add_session_content, name='add_session_content'),
    path('sessions/<int:session_id>/attendance/', views.mark_attendance, name='mark_attendance'),
    path('sessions/<int:session_id>/add-participant/', views.add_participant, name='add_participant'),
    
    # Regular Session Management URLs
    path('sessions/<int:session_id>/start/', views.start_session, name='start_session'),
    path('sessions/<int:session_id>/complete/', views.complete_session, name='complete_session'),
    path('sessions/<int:session_id>/cancel/', views.cancel_session, name='cancel_session'),
    
    # Zoom Integration URLs
    path('sessions/<int:session_id>/start-zoom/', views.start_zoom_session, name='start_zoom_session'),
    path('sessions/<int:session_id>/zoom-data/', views.get_zoom_session_data, name='zoom_session_data'),
    path('sessions/<int:session_id>/notify-participants/', views.notify_zoom_participants, name='notify_zoom_participants'),
    path('sessions/<int:session_id>/join-zoom/', views.join_zoom_meeting, name='join_zoom_meeting'),
    
    # Test URL for debugging Zoom
    path('sessions/<int:session_id>/test-zoom/', views.test_zoom_data, name='test_zoom_data'),
    
    # AJAX endpoints
    path('ajax/member/<int:member_id>/assignments/', views.get_member_assignments, name='get_member_assignments'),
    path('ajax/calendar-data/', views.session_calendar_data, name='session_calendar_data'),
]