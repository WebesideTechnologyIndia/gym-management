# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User, Gym, GymAdmin, Member, MembershipPlan, Membership, Payment

# Custom User Admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'user_type', 'phone', 'is_active', 'created_at')
    list_filter = ('user_type', 'is_active', 'is_staff', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone', 'created_at'),
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

# Gym Admin
@admin.register(Gym)
class GymModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'is_active', 'member_count', 'registration_date', 'created_by')
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
        return obj.members.count()
    member_count.short_description = 'Total Members'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by').prefetch_related('members')

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
    list_display = ('full_name', 'phone', 'gym', 'age', 'gender', 'is_active', 'created_at')
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
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'gym')

# Membership Plan Admin
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

# Membership Admin
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

# Payment Admin
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