from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from .models import User, Gym, Member
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Username", "id": "username"}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password", "id": "password"}
        )
    )


class GymCreationForm(forms.ModelForm):
    admin_username = forms.CharField(max_length=150)
    admin_email = forms.EmailField()
    admin_password = forms.CharField(widget=forms.PasswordInput())
    admin_phone = forms.CharField(max_length=15, required=False)

    class Meta:
        model = Gym
        fields = ["name", "address", "phone", "email"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


# forms.py - Membership wala saara scene hata diya
import re
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date

User = get_user_model()


class MemberCreationForm(forms.Form):
    # Account Information
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter first name"}
        ),
    )

    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter last name"}
        ),
    )

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Choose username"}
        ),
    )

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Enter email address"}
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Enter password"}
        ),
        min_length=8,
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm password"}
        )
    )

    # Personal Information
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )

    GENDER_CHOICES = [
        ("", "Select Gender"),
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    ]

    gender = forms.ChoiceField(
        choices=GENDER_CHOICES, widget=forms.Select(attrs={"class": "form-select"})
    )

    BLOOD_GROUP_CHOICES = [
        ("", "Select Blood Group"),
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
    ]

    blood_group = forms.ChoiceField(
        choices=BLOOD_GROUP_CHOICES, widget=forms.Select(attrs={"class": "form-select"})
    )

    phone = forms.CharField(
        max_length=10,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "9876543210",
                "pattern": "[0-9]{10}",
            }
        ),
    )

    alternate_phone = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "9876543210 (Optional)",
                "pattern": "[0-9]{10}",
            }
        ),
    )

    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
    )

    # Address Information
    address_line1 = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "House No, Street Name"}
        ),
    )

    address_line2 = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Landmark, Area (Optional)"}
        ),
    )

    city = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "City"}),
    )

    state = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "State"}),
    )

    pin_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "123456",
                "pattern": "[0-9]{6}",
            }
        ),
    )

    # Medical Information
    medical_conditions = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Any medical conditions (Optional)",
                "rows": 3,
            }
        ),
    )

    medications = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Current medications (Optional)",
                "rows": 3,
            }
        ),
    )

    previous_injuries = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Previous injuries (Optional)",
                "rows": 3,
            }
        ),
    )

    # Emergency Contacts
    emergency_contact_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Emergency contact name"}
        ),
    )

    emergency_contact_phone = forms.CharField(
        max_length=10,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "9876543210",
                "pattern": "[0-9]{10}",
            }
        ),
    )

    RELATION_CHOICES = [
        ("", "Select Relationship"),
        ("father", "Father"),
        ("mother", "Mother"),
        ("spouse", "Spouse"),
        ("brother", "Brother"),
        ("sister", "Sister"),
        ("friend", "Friend"),
        ("other", "Other"),
    ]

    emergency_contact_relation = forms.ChoiceField(
        choices=RELATION_CHOICES, widget=forms.Select(attrs={"class": "form-select"})
    )

    emergency_contact_address = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Emergency contact address (Optional)",
            }
        ),
    )

    # Secondary Emergency Contact (Optional)
    emergency_contact_name2 = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Second emergency contact (Optional)",
            }
        ),
    )

    emergency_contact_phone2 = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "9876543210 (Optional)",
                "pattern": "[0-9]{10}",
            }
        ),
    )

    emergency_contact_relation2 = forms.ChoiceField(
        choices=RELATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists!")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists!")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone and not re.match(r"^\d{10}$", phone):
            raise ValidationError("Phone number must be 10 digits!")
        # Check if phone exists - adjust this based on your User model
        if hasattr(User, "phone") and User.objects.filter(phone=phone).exists():
            raise ValidationError("Phone number already exists!")
        return phone

    def clean_alternate_phone(self):
        alternate_phone = self.cleaned_data.get("alternate_phone")
        if alternate_phone and not re.match(r"^\d{10}$", alternate_phone):
            raise ValidationError("Alternate phone number must be 10 digits!")
        return alternate_phone

    def clean_emergency_contact_phone(self):
        phone = self.cleaned_data.get("emergency_contact_phone")
        if phone and not re.match(r"^\d{10}$", phone):
            raise ValidationError("Emergency contact phone must be 10 digits!")
        return phone

    def clean_emergency_contact_phone2(self):
        phone = self.cleaned_data.get("emergency_contact_phone2")
        if phone and not re.match(r"^\d{10}$", phone):
            raise ValidationError("Second emergency contact phone must be 10 digits!")
        return phone

    def clean_pin_code(self):
        pin_code = self.cleaned_data.get("pin_code")
        if pin_code and not re.match(r"^\d{6}$", pin_code):
            raise ValidationError("PIN code must be 6 digits!")
        return pin_code

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if dob:
            today = date.today()
            age = (
                today.year
                - dob.year
                - ((today.month, today.day) < (dob.month, dob.day))
            )
            if age < 16:
                raise ValidationError("Member must be at least 16 years old!")
            if age > 100:
                raise ValidationError("Please enter a valid date of birth!")
        return dob

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match!")

        return cleaned_data


# forms.py
from django import forms
from .models import Membership, MembershipPlan


class MembershipPlanForm(forms.ModelForm):
    class Meta:
        model = MembershipPlan
        fields = ["name", "duration_months", "price", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Gold Plan"}
            ),
            "duration_months": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "e.g. 6"}
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "e.g. 5000",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Plan description...",
                }
            ),
        }


# Add this to your forms.py

from django import forms
from django.utils import timezone
from .models import Membership, MembershipPlan, Member, Payment


class MembershipForm(forms.ModelForm):
    # Payment fields
    payment_type = forms.ChoiceField(
        choices=[("full", "Full Payment"), ("partial", "Partial Payment")],
        widget=forms.RadioSelect,
        initial="full",
    )
    partial_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "0.01", "min": "1"}
        ),
    )
    payment_method = forms.ChoiceField(
        choices=[
            ("", "Select Payment Method"),
            ("cash", "Cash"),
            ("card", "Credit/Debit Card"),
            ("upi", "UPI"),
            ("net_banking", "Net Banking"),
            ("cheque", "Cheque"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    payment_notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Any payment notes...",
            }
        ),
    )
    next_payment_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    class Meta:
        model = Membership
        fields = ["member_name", "plan", "start_date"]
        widgets = {
            "member_name": forms.Select(attrs={"class": "form-select"}),
            "plan": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "value": timezone.now().date(),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        gym = kwargs.pop("gym", None)
        super().__init__(*args, **kwargs)

        if gym:
            # Filter members by gym
            self.fields["member_name"].queryset = Member.objects.filter(
                gym=gym, is_active=True
            ).order_by("user__first_name", "user__last_name")

            # Update member_name choices to show full names
            self.fields["member_name"].choices = [("", "Select Member")] + [
                (member.id, f"{member.user.get_full_name()} ({member.user.username})")
                for member in self.fields["member_name"].queryset
            ]
        else:
            self.fields["member_name"].queryset = Member.objects.none()

        # Filter active plans
        self.fields["plan"].queryset = MembershipPlan.objects.filter(is_active=True)

        # Update plan choices to show price
        self.fields["plan"].choices = [("", "Select Plan")] + [
            (plan.id, f"{plan.name} - ₹{plan.price} ({plan.duration_months} months)")
            for plan in self.fields["plan"].queryset
        ]

    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get("payment_type")
        partial_amount = cleaned_data.get("partial_amount")
        plan = cleaned_data.get("plan")
        payment_method = cleaned_data.get("payment_method")
        next_payment_date = cleaned_data.get("next_payment_date")

        # Validate payment method
        if not payment_method:
            raise forms.ValidationError("Payment method is required.")

        # Validate partial payment
        if payment_type == "partial":
            if not partial_amount:
                raise forms.ValidationError(
                    "Partial amount is required for partial payments."
                )

            if plan and partial_amount:
                if partial_amount <= 0:
                    raise forms.ValidationError(
                        "Partial amount must be greater than 0."
                    )
                if partial_amount >= plan.price:
                    raise forms.ValidationError(
                        "Partial amount cannot be equal to or greater than plan price."
                    )

            if not next_payment_date:
                raise forms.ValidationError(
                    "Next payment reminder date is required for partial payments."
                )

            # Check if reminder date is in the future
            if next_payment_date and next_payment_date <= timezone.now().date():
                raise forms.ValidationError(
                    "Next payment reminder must be a future date."
                )

        return cleaned_data


# Form for adding additional payments
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "payment_method", "notes", "next_payment_reminder"]
        widgets = {
            "amount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "1"}
            ),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Payment notes...",
                }
            ),
            "next_payment_reminder": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }

    def __init__(self, *args, **kwargs):
        membership = kwargs.pop("membership", None)
        super().__init__(*args, **kwargs)

        if membership:
            self.fields["amount"].widget.attrs["max"] = str(membership.remaining_amount)
            self.fields["amount"].help_text = (
                f"Maximum amount: ₹{membership.remaining_amount}"
            )

        # Update payment method choices
        self.fields["payment_method"].choices = [
            ("", "Select Payment Method"),
            ("cash", "Cash"),
            ("card", "Credit/Debit Card"),
            ("upi", "UPI"),
            ("net_banking", "Net Banking"),
            ("cheque", "Cheque"),
        ]

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0.")
        return amount

    def clean_next_payment_reminder(self):
        reminder_date = self.cleaned_data.get("next_payment_reminder")
        if reminder_date and reminder_date <= timezone.now().date():
            raise forms.ValidationError("Reminder date must be in the future.")
        return reminder_date
