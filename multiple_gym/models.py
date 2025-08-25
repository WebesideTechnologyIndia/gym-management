from django.db import models
from decimal import Decimal
# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    USER_TYPES = (
        ('superadmin', 'Super Admin'),
        ('gymadmin', 'Gym Admin'),
        ('member', 'Member'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='member')
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Gym(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    registration_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'superadmin'})
    
    def __str__(self):
        return self.name

class GymAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'gymadmin'})
    gyms = models.ManyToManyField(Gym, related_name='admins')
    
    def __str__(self):
        return f"{self.user.username} - Admin"

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date

class Member(models.Model):
    # Link to custom User model
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'user_type': 'member'})
    gym = models.ForeignKey('Gym', on_delete=models.CASCADE, related_name='members')
    
    # Personal Information
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    phone = models.CharField(max_length=10, unique=True)
    alternate_phone = models.CharField(max_length=10, blank=True, null=True)
    photo = models.ImageField(upload_to='member_photos/', blank=True, null=True)
    
    # Address Information
    address_line1 = models.CharField(max_length=100)
    address_line2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pin_code = models.CharField(max_length=6)
    
    # Medical Information
    medical_conditions = models.TextField(blank=True, help_text="Any medical conditions")
    medications = models.TextField(blank=True, help_text="Current medications")
    previous_injuries = models.TextField(blank=True, help_text="Previous injuries")
    
    # Emergency Contacts
    RELATION_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('spouse', 'Spouse'),
        ('brother', 'Brother'),
        ('sister', 'Sister'),
        ('friend', 'Friend'),
        ('other', 'Other')
    ]
    
    # Primary Emergency Contact
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=10)
    emergency_contact_relation = models.CharField(max_length=20, choices=RELATION_CHOICES)
    emergency_contact_address = models.TextField(blank=True)
    
    # Secondary Emergency Contact (Optional)
    emergency_contact_name2 = models.CharField(max_length=100, blank=True)
    emergency_contact_phone2 = models.CharField(max_length=10, blank=True)
    emergency_contact_relation2 = models.CharField(max_length=20, choices=RELATION_CHOICES, blank=True)
    
    # Membership Information
    MEMBERSHIP_PLAN_CHOICES = [
        ('1_month', '1 Month Plan'),
        ('3_months', '3 Months Plan'),
        ('6_months', '6 Months Plan'),
        ('12_months', '1 Year Plan'),
    ]
    
    # membership_plan = models.CharField(max_length=20, choices=MEMBERSHIP_PLAN_CHOICES)
    # membership_start_date = models.DateField(default=timezone.now)
    # membership_end_date = models.DateField()
    # membership_months = models.IntegerField(default=1, help_text="Duration in months")
    
    # Discount Options
    # is_student = models.BooleanField(default=False, help_text="Student discount applicable")
    # is_corporate = models.BooleanField(default=False, help_text="Corporate discount applicable")
    # is_family_member = models.BooleanField(default=False, help_text="Family member discount applicable")
    
    # Status and Tracking
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Member"
        verbose_name_plural = "Members"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.gym.name}"
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    # @property
    # def is_membership_active(self):
    #     """Check if membership is currently active"""
    #     from datetime import date
    #     return self.is_active and self.membership_end_date >= date.today()
    
    # @property
    # def days_remaining(self):
    #     """Calculate days remaining in membership"""
    #     if self.membership_end_date:
    #         from datetime import date
    #         remaining = (self.membership_end_date - date.today()).days
    #         return max(0, remaining)
    #     return 0
    
    # def save(self, *args, **kwargs):
    #     # Auto-calculate membership end date based on plan and start date
    #     if self.membership_start_date and self.membership_months:
    #         from datetime import timedelta
    #         from dateutil.relativedelta import relativedelta
    #         self.membership_end_date = self.membership_start_date + relativedelta(months=self.membership_months)
        
        super().save(*args, **kwargs)



# models.py
# models.py - CORRECTED Membership model
from django.db import models
from django.utils import timezone
from datetime import timedelta

class MembershipPlan(models.Model):
    name = models.CharField(max_length=100)
    duration_months = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.name} - {self.duration_months} months"


# Updated Membership model - Replace your existing Membership model with this
from django.db import models
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

class Membership(models.Model):
    MEMBERSHIP_STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending Payment'),
    ]
    
    member_name = models.ForeignKey('Member', on_delete=models.CASCADE, related_name='memberships')
    plan = models.ForeignKey('MembershipPlan', on_delete=models.CASCADE)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    
    # Payment status
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=[
        ('paid', 'Fully Paid'),
        ('partial', 'Partially Paid'),
        ('unpaid', 'Unpaid'),
    ], default='unpaid')
    
    is_active = models.BooleanField(default=True)
    membership_status = models.CharField(max_length=20, choices=MEMBERSHIP_STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Set total amount from plan price - ensure it's Decimal
        if not self.total_amount:
            self.total_amount = Decimal(str(self.plan.price))
        
        # Calculate end date if not set
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_months * 30)
        
        # Calculate remaining amount - ensure both are Decimal
        self.remaining_amount = Decimal(str(self.total_amount)) - Decimal(str(self.paid_amount))
        
        # Update payment status
        if Decimal(str(self.paid_amount)) >= Decimal(str(self.total_amount)):
            self.payment_status = 'paid'
            self.membership_status = 'active'
        elif Decimal(str(self.paid_amount)) > 0:
            self.payment_status = 'partial'
            self.membership_status = 'pending'
        else:
            self.payment_status = 'unpaid'
            self.membership_status = 'pending'
        
        super().save(*args, **kwargs)
    
    @property
    def is_fully_paid(self):
        return Decimal(str(self.paid_amount)) >= Decimal(str(self.total_amount))
    
    @property
    def payment_percentage(self):
        if self.total_amount > 0:
            return (Decimal(str(self.paid_amount)) / Decimal(str(self.total_amount))) * 100
        return 0
    
    def __str__(self):
        return f"{self.member_name.user.username} - {self.plan.name} ({self.payment_status})"
    
# Add these models to your existing models.py

from django.db import models
from django.utils import timezone
from datetime import timedelta

# Payment model to track all payments
class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
        ('net_banking', 'Net Banking'),
        ('cheque', 'Cheque'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('full', 'Full Payment'),
        ('partial', 'Partial Payment'),
        ('installment', 'Installment'),
    ]
    
    membership = models.ForeignKey('Membership', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='full')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='completed')
    payment_date = models.DateTimeField(default=timezone.now)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # For partial payments
    next_payment_reminder = models.DateField(blank=True, null=True)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_by = models.ForeignKey('User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.membership.member_name.user.username} - ₹{self.amount} ({self.payment_type})"