# multiple_gym/admin.py - Updated with Trainer Management
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User, Gym, GymAdmin, Member, MembershipPlan, Membership, Payment

# Import trainer models
from trainer_management.models import (
    Trainer, TrainerPermission, MemberTrainerAssignment,
    TrainingSession, SessionParticipant, SessionContent, SessionAttendance
)


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Gym, GymAdmin, Member, MembershipPlan, Membership, Payment

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'user_type_badge', 'phone', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('user_type', 'phone'),
        }),
    )
    
    def user_type_badge(self, obj):
        colors = {
            'superadmin': '#dc3545',
            'gymadmin': '#0d6efd', 
            'trainer': '#198754',
            'member': '#6f42c1'
        }
        color = colors.get(obj.user_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_user_type_display()
        )
    user_type_badge.short_description = 'User Type'

    
# ... aur bhi models
# Custom User Admin
# @admin.register(User)
# class UserAdmin(BaseUserAdmin):
#     list_display = ('username', 'email', 'user_type_badge', 'phone', 'is_active', 'created_at')
#     list_filter = ('user_type', 'is_active', 'is_staff', 'created_at')
#     search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
#     ordering = ('-created_at',)
    
#     fieldsets = BaseUserAdmin.fieldsets + (
#         ('Additional Info', {
#             'fields': ('user_type', 'phone', 'created_at'),
#         }),
#     )
    
#     readonly_fields = ('created_at',)
    
#     def user_type_badge(self, obj):
#         colors = {
#             'superadmin': '#dc3545',  # Red
#             'gymadmin': '#0d6efd',    # Blue
#             'trainer': '#198754',     # Green
#             'member': '#6f42c1'       # Purple
#         }
#         color = colors.get(obj.user_type, '#6c757d')
#         return format_html(
#             '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
#             color,
#             obj.get_user_type_display()
#         )
#     user_type_badge.short_description = 'User Type'
    
#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related()

# Gym Admin
@admin.register(Gym)
class GymModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'is_active', 'member_count', 'trainer_count', 'registration_date', 'created_by')
    list_filter = ('is_active', 'registration_date')
    search_fields = ('name', 'phone', 'email', 'address')
    ordering = ('-registration_date',)
    readonly_fields = ('registration_date',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'phone', 'email')
        }),
        ('Address', {
            'fields': ('address',)
        }),
        ('Status & Admin', {
            'fields': ('is_active', 'created_by', 'registration_date')
        }),
    )
    
    def member_count(self, obj):
        count = obj.members.count()
        return format_html('<span style="color: #0d6efd; font-weight: bold;">{}</span>', count)
    member_count.short_description = 'Members'
    
    def trainer_count(self, obj):
        count = obj.trainers.filter(is_active=True).count()
        return format_html('<span style="color: #198754; font-weight: bold;">{}</span>', count)
    trainer_count.short_description = 'Trainers'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by').prefetch_related('members', 'trainers')

# Gym Admin (Staff) Admin
@admin.register(GymAdmin)
class GymAdminModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_email', 'gym_list', 'gym_count')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    filter_horizontal = ('gyms',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def gym_list(self, obj):
        gyms = obj.gyms.all()[:3]  # Show first 3 gyms
        gym_names = [gym.name for gym in gyms]
        if obj.gyms.count() > 3:
            gym_names.append(f"... and {obj.gyms.count() - 3} more")
        return ", ".join(gym_names)
    gym_list.short_description = 'Gyms Managed'
    
    def gym_count(self, obj):
        return obj.gyms.count()
    gym_count.short_description = 'Total Gyms'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('gyms')

# Member Admin
@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'gym', 'age', 'gender', 'assigned_trainer', 'is_active', 'created_at')
    list_filter = ('gym', 'gender', 'blood_group', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone', 'alternate_phone')
    ordering = ('-created_at',)
    readonly_fields = ('age', 'created_at', 'updated_at')
    
    fieldsets = (
        ('User Account', {
            'fields': ('user', 'gym')
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'age', 'gender', 'blood_group', 'photo')
        }),
        ('Contact Information', {
            'fields': ('phone', 'alternate_phone')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'pin_code')
        }),
        ('Medical Information', {
            'fields': ('medical_conditions', 'medications', 'previous_injuries'),
            'classes': ('collapse',)
        }),
        ('Emergency Contacts', {
            'fields': (
                ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation'),
                'emergency_contact_address',
                ('emergency_contact_name2', 'emergency_contact_phone2', 'emergency_contact_relation2')
            ),
            'classes': ('collapse',)
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'
    
    def assigned_trainer(self, obj):
        assignments = obj.trainer_assignments.filter(is_active=True)
        if assignments.exists():
            trainer_names = [assignment.trainer.user.get_full_name() for assignment in assignments[:2]]
            if assignments.count() > 2:
                trainer_names.append(f"... +{assignments.count() - 2} more")
            return format_html('<span style="color: #198754;">{}</span>', ", ".join(trainer_names))
        return format_html('<span style="color: #6c757d;">Not assigned</span>')
    assigned_trainer.short_description = 'Assigned Trainer(s)'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'gym').prefetch_related('trainer_assignments__trainer__user')

# 🔥 TRAINER MODELS ADMIN - NEW ADDITIONS

@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = [
        'user_full_name', 'user_email', 'gym', 'phone', 'specialization', 
        'experience_years', 'assigned_members_count', 'salary_info', 'is_active', 'hire_date'
    ]
    list_filter = ['gym', 'is_active', 'salary_type', 'gender', 'hire_date', 'experience_years']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email', 'phone', 'specialization']
    raw_id_fields = ['user', 'created_by']
    readonly_fields = ['age', 'assigned_members_count', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User Account', {
            'fields': ('user', 'gym')
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'age', 'gender', 'phone', 'alternate_phone', 'photo')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'pin_code'),
            'classes': ('collapse',)
        }),
        ('Professional Information', {
            'fields': ('specialization', 'certifications', 'experience_years', 'bio', 'hire_date')
        }),
        ('Salary Information', {
            'fields': ('salary_type', 'salary_amount')
        }),
        ('Statistics', {
            'fields': ('assigned_members_count',),
            'classes': ('collapse',)
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_full_name.short_description = 'Full Name'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def assigned_members_count(self, obj):
        count = obj.assigned_members.filter(is_active=True).count()
        return format_html('<span style="color: #0d6efd; font-weight: bold;">{}</span>', count)
    assigned_members_count.short_description = 'Assigned Members'
    
    def salary_info(self, obj):
        return f"₹{obj.salary_amount} ({obj.get_salary_type_display()})"
    salary_info.short_description = 'Salary'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'gym', 'created_by').prefetch_related('assigned_members')

@admin.register(TrainerPermission)
class TrainerPermissionAdmin(admin.ModelAdmin):
    list_display = ['trainer_name', 'trainer_gym', 'member_perms', 'session_perms', 'report_perms', 'updated_at']
    list_filter = [
        'can_create_sessions', 'can_create_members', 'can_upload_content', 
        'can_view_reports', 'trainer__gym'
    ]
    search_fields = ['trainer__user__first_name', 'trainer__user__last_name', 'trainer__user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Trainer', {
            'fields': ('trainer',)
        }),
        ('Member Management Permissions', {
            'fields': ('can_create_members', 'can_edit_members', 'can_view_all_members', 'can_manage_assignments')
        }),
        ('Session Management Permissions', {
            'fields': ('can_create_sessions', 'can_edit_sessions', 'can_delete_sessions', 'can_upload_content')
        }),
        ('Reporting Permissions', {
            'fields': ('can_view_reports', 'can_view_payments')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def trainer_name(self, obj):
        return obj.trainer.user.get_full_name() or obj.trainer.user.username
    trainer_name.short_description = 'Trainer'
    
    def trainer_gym(self, obj):
        return obj.trainer.gym.name
    trainer_gym.short_description = 'Gym'
    
    def member_perms(self, obj):
        perms = []
        if obj.can_create_members: perms.append('Create')
        if obj.can_edit_members: perms.append('Edit')
        if obj.can_view_all_members: perms.append('View All')
        if obj.can_manage_assignments: perms.append('Assign')
        return ', '.join(perms) if perms else 'None'
    member_perms.short_description = 'Member Permissions'
    
    def session_perms(self, obj):
        perms = []
        if obj.can_create_sessions: perms.append('Create')
        if obj.can_edit_sessions: perms.append('Edit')
        if obj.can_delete_sessions: perms.append('Delete')
        if obj.can_upload_content: perms.append('Upload')
        return ', '.join(perms) if perms else 'None'
    session_perms.short_description = 'Session Permissions'
    
    def report_perms(self, obj):
        perms = []
        if obj.can_view_reports: perms.append('Reports')
        if obj.can_view_payments: perms.append('Payments')
        return ', '.join(perms) if perms else 'None'
    report_perms.short_description = 'Report Permissions'

@admin.register(MemberTrainerAssignment)
class MemberTrainerAssignmentAdmin(admin.ModelAdmin):
    list_display = ['member_name', 'trainer_name', 'assignment_type_badge', 'assigned_date', 'is_active']
    list_filter = ['assignment_type', 'is_active', 'assigned_date', 'trainer__gym']
    search_fields = [
        'member__user__first_name', 'member__user__last_name', 
        'trainer__user__first_name', 'trainer__user__last_name'
    ]
    raw_id_fields = ['member', 'trainer', 'created_by']
    readonly_fields = ['is_ongoing', 'created_at']
    ordering = ['-assigned_date']
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('member', 'trainer', 'assignment_type', 'assigned_date', 'end_date')
        }),
        ('Goals & Notes', {
            'fields': ('goals', 'notes')
        }),
        ('Status', {
            'fields': ('is_active', 'is_ongoing')
        }),
        ('System Info', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def member_name(self, obj):
        return obj.member.user.get_full_name() or obj.member.user.username
    member_name.short_description = 'Member'
    
    def trainer_name(self, obj):
        return obj.trainer.user.get_full_name() or obj.trainer.user.username
    trainer_name.short_description = 'Trainer'
    
    def assignment_type_badge(self, obj):
        colors = {
            'weight_loss': '#dc3545',
            'muscle_gain': '#198754',
            'fitness': '#0d6efd',
            'strength': '#fd7e14',
            'cardio': '#e83e8c',
            'rehabilitation': '#6f42c1',
            'sport_specific': '#20c997',
            'other': '#6c757d'
        }
        color = colors.get(obj.assignment_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_assignment_type_display()
        )
    assignment_type_badge.short_description = 'Assignment Type'

@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'trainer_name', 'session_date', 'start_time', 'session_type_badge', 
        'participants_count', 'status_badge', 'difficulty_level'
    ]
    list_filter = ['status', 'session_type', 'difficulty_level', 'trainer__gym', 'session_date']
    search_fields = ['title', 'description', 'trainer__user__first_name', 'trainer__user__last_name']
    readonly_fields = ['participants_count', 'available_spots', 'is_past', 'is_today', 'created_at', 'updated_at']
    ordering = ['-session_date', '-start_time']
    date_hierarchy = 'session_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'trainer', 'session_type')
        }),
        ('Schedule', {
            'fields': ('session_date', 'start_time', 'end_time', 'duration_minutes', 'location')
        }),
        ('Participants', {
            'fields': ('max_participants', 'participants_count', 'available_spots')
        }),
        ('Workout Details', {
            'fields': ('difficulty_level', 'equipment_needed', 'workout_plan'),
            'classes': ('collapse',)
        }),
        ('Exercise Plan', {
            'fields': ('warm_up_exercises', 'main_exercises', 'cool_down_exercises'),
            'classes': ('collapse',)
        }),
        ('Session Notes', {
            'fields': ('pre_session_notes', 'post_session_notes', 'trainer_feedback'),
            'classes': ('collapse',)
        }),
        ('Status & Timestamps', {
            'fields': ('status', 'is_past', 'is_today', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def trainer_name(self, obj):
        return obj.trainer.user.get_full_name() or obj.trainer.user.username
    trainer_name.short_description = 'Trainer'
    
    def session_type_badge(self, obj):
        colors = {
            'individual': '#0d6efd',
            'group': '#198754',
            'class': '#fd7e14',
            'online': '#e83e8c',
            'assessment': '#6f42c1'
        }
        color = colors.get(obj.session_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_session_type_display()
        )
    session_type_badge.short_description = 'Type'
    
    def status_badge(self, obj):
        colors = {
            'scheduled': '#6c757d',
            'active': '#fd7e14',
            'completed': '#198754',
            'cancelled': '#dc3545',
            'rescheduled': '#e83e8c'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

@admin.register(SessionParticipant)
class SessionParticipantAdmin(admin.ModelAdmin):
    list_display = ['session_title', 'member_name', 'enrolled_at', 'attended_badge', 'performance_rating']
    list_filter = ['attended', 'performance_rating', 'enrolled_at', 'session__trainer__gym']
    search_fields = [
        'session__title', 'member__user__first_name', 'member__user__last_name'
    ]
    readonly_fields = ['enrolled_at', 'attendance_marked_at']
    ordering = ['-enrolled_at']
    
    def session_title(self, obj):
        return obj.session.title
    session_title.short_description = 'Session'
    
    def member_name(self, obj):
        return obj.member.user.get_full_name() or obj.member.user.username
    member_name.short_description = 'Member'
    
    def attended_badge(self, obj):
        if obj.attended:
            return format_html('<span style="color: #198754; font-weight: bold;">✓ Present</span>')
        return format_html('<span style="color: #dc3545; font-weight: bold;">✗ Absent</span>')
    attended_badge.short_description = 'Attendance'

@admin.register(SessionContent)
class SessionContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'session_title', 'content_type_badge', 'order', 'is_required', 'is_public', 'uploaded_by']
    list_filter = ['content_type', 'is_required', 'is_public', 'created_at']
    search_fields = ['title', 'description', 'session__title']
    readonly_fields = ['file_size_formatted', 'created_at', 'updated_at']
    ordering = ['session', 'order', '-created_at']
    
    def session_title(self, obj):
        return obj.session.title
    session_title.short_description = 'Session'
    
    def content_type_badge(self, obj):
        colors = {
            'pdf': '#dc3545',
            'video': '#0d6efd',
            'youtube': '#dc3545',
            'image': '#198754',
            'audio': '#fd7e14',
            'link': '#6f42c1',
            'text': '#6c757d'
        }
        color = colors.get(obj.content_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_content_type_display()
        )
    content_type_badge.short_description = 'Type'

# Membership Plan Admin (Updated)
@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_months', 'formatted_price', 'is_active', 'member_count')
    list_filter = ('duration_months', 'is_active')
    search_fields = ('name', 'description')
    ordering = ('duration_months', 'price')
    
    def formatted_price(self, obj):
        return f"₹{obj.price:,.2f}"
    formatted_price.short_description = 'Price'
    
    def member_count(self, obj):
        return obj.membership_set.count()
    member_count.short_description = 'Active Memberships'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('membership_set')

# Membership Admin (Updated)
@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('member_name', 'plan', 'start_date', 'end_date', 'payment_status_badge', 'membership_status', 'payment_progress')
    list_filter = ('payment_status', 'membership_status', 'is_active', 'plan', 'created_at')
    search_fields = ('member_name__user__username', 'member_name__user__first_name', 'member_name__user__last_name', 'member_name__phone')
    ordering = ('-created_at',)
    readonly_fields = ('payment_percentage', 'is_fully_paid', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Membership Details', {
            'fields': ('member_name', 'plan', 'start_date', 'end_date')
        }),
        ('Payment Information', {
            'fields': (
                ('total_amount', 'paid_amount', 'remaining_amount'),
                ('payment_status', 'payment_percentage', 'is_fully_paid')
            )
        }),
        ('Status', {
            'fields': ('is_active', 'membership_status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def payment_status_badge(self, obj):
        colors = {
            'paid': 'green',
            'partial': 'orange',
            'unpaid': 'red'
        }
        color = colors.get(obj.payment_status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Payment Status'
    
    def payment_progress(self, obj):
        percentage = obj.payment_percentage
        color = 'green' if percentage == 100 else 'orange' if percentage > 0 else 'red'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{}%</div></div>',
            percentage, color, int(percentage)
        )
    payment_progress.short_description = 'Payment Progress'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('member_name__user', 'plan')

# Payment Admin (Updated)
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('membership_member', 'formatted_amount', 'payment_method', 'payment_type', 'payment_status_badge', 'payment_date', 'created_by')
    list_filter = ('payment_status', 'payment_method', 'payment_type', 'payment_date')
    search_fields = ('membership__member_name__user__username', 'transaction_id', 'notes')
    ordering = ('-payment_date',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('membership', 'amount', 'payment_type', 'payment_method')
        }),
        ('Transaction Info', {
            'fields': ('payment_status', 'payment_date', 'transaction_id')
        }),
        ('Additional Info', {
            'fields': ('notes', 'next_payment_reminder', 'remaining_amount'),
            'classes': ('collapse',)
        }),
        ('Admin Info', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def membership_member(self, obj):
        return f"{obj.membership.member_name.user.get_full_name()}"
    membership_member.short_description = 'Member'
    
    def formatted_amount(self, obj):
        return f"₹{obj.amount:,.2f}"
    formatted_amount.short_description = 'Amount'
    
    def payment_status_badge(self, obj):
        colors = {
            'completed': 'green',
            'pending': 'orange',
            'failed': 'red',
            'cancelled': 'gray'
        }
        color = colors.get(obj.payment_status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('membership__member_name__user', 'created_by')

# Custom admin site configuration
admin.site.site_header = "Gym Management System"
admin.site.site_title = "Gym Admin"
admin.site.index_title = "Welcome to Gym Management System"

# Optional: Add some custom actions
def activate_selected(modeladmin, request, queryset):
    queryset.update(is_active=True)
activate_selected.short_description = "Activate selected items"

def deactivate_selected(modeladmin, request, queryset):
    queryset.update(is_active=False)
deactivate_selected.short_description = "Deactivate selected items"

# Add actions to relevant models
GymModelAdmin.actions = [activate_selected, deactivate_selected]
MemberAdmin.actions = [activate_selected, deactivate_selected]
MembershipAdmin.actions = [activate_selected, deactivate_selected]
TrainerAdmin.actions = [activate_selected, deactivate_selected]