# from django.contrib import admin

# # Register your models here.
# # trainer_management/admin.py
# from django.contrib import admin
# from .models import (
#     Trainer, TrainerPermission, MemberTrainerAssignment,
#     TrainingSession, SessionParticipant, SessionContent, SessionAttendance
# )

# @admin.register(Trainer)
# class TrainerAdmin(admin.ModelAdmin):
#     list_display = ['user', 'gym', 'phone', 'specialization', 'experience_years', 'is_active', 'hire_date']
#     list_filter = ['gym', 'is_active', 'salary_type', 'gender']
#     search_fields = ['user__first_name', 'user__last_name', 'phone', 'specialization']
#     raw_id_fields = ['user', 'created_by']
#     readonly_fields = ['created_at', 'updated_at']

# @admin.register(TrainerPermission)
# class TrainerPermissionAdmin(admin.ModelAdmin):
#     list_display = ['trainer', 'can_create_sessions', 'can_create_members', 'can_upload_content']
#     list_filter = ['can_create_sessions', 'can_create_members', 'can_upload_content']

# @admin.register(MemberTrainerAssignment)
# class MemberTrainerAssignmentAdmin(admin.ModelAdmin):
#     list_display = ['member', 'trainer', 'assignment_type', 'assigned_date', 'is_active']
#     list_filter = ['assignment_type', 'is_active', 'assigned_date']
#     search_fields = ['member__user__first_name', 'trainer__user__first_name']

# @admin.register(TrainingSession)
# class TrainingSessionAdmin(admin.ModelAdmin):
#     list_display = ['title', 'trainer', 'session_date', 'start_time', 'status', 'session_type']
#     list_filter = ['status', 'session_type', 'difficulty_level', 'session_date']
#     search_fields = ['title', 'trainer__user__first_name']
#     readonly_fields = ['created_at', 'updated_at']

# @admin.register(SessionContent)
# class SessionContentAdmin(admin.ModelAdmin):
#     list_display = ['title', 'session', 'content_type', 'is_required', 'order']
#     list_filter = ['content_type', 'is_required', 'is_public']
#     search_fields = ['title', 'session__title']
