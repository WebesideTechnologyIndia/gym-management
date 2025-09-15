from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from decimal import Decimal

from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from datetime import timedelta
from .models import User, Gym, GymAdmin, Member, Membership, MembershipPlan, Payment
from .forms import (
    CustomLoginForm,
    GymCreationForm,
    MemberCreationForm,
    MembershipForm,
    MembershipPlanForm,
)

User = get_user_model()

@csrf_protect
def login_view(request):
    print(f"=== LOGIN VIEW DEBUG ===")
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"Request method: {request.method}")
    print(f"Request path: {request.path}")

    if request.user.is_authenticated:
        print(f"User: {request.user}")
        print(f"User type: {getattr(request.user, 'user_type', 'NO USER_TYPE ATTRIBUTE')}")
        print(f"User ID: {request.user.id}")

        # Check if user has user_type attribute
        if hasattr(request.user, "user_type"):
            user_type = request.user.user_type
            print(f"Redirecting to dashboard for user_type: {user_type}")

            if user_type == "superadmin":
                return redirect("multiple_gym:superadmin_dashboard")  # ADD NAMESPACE
            elif user_type == "gymadmin":
                return redirect("multiple_gym:gymadmin_home")  # ADD NAMESPACE
            elif user_type == "member":
                print("Redirecting to member_dashboard")
                return redirect("multiple_gym:member_dashboard")  # ADD NAMESPACE
            elif user_type == "trainer":
                print("Redirecting to trainer_dashboard")
                return redirect("trainer_management:trainer_dashboard")
            else:
                print(f"Invalid user type: {user_type}")
                logout(request)
                messages.error(request, "Invalid user type. Please contact admin.")
                return redirect("multiple_gym:login")  # ADD NAMESPACE
        else:
            print("User does not have user_type attribute")
            logout(request)
            messages.error(request, "User profile incomplete. Please contact admin.")
            return redirect("multiple_gym:login")  # ADD NAMESPACE

    if request.method == "POST":
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome {user.username}!")
                print(f"User logged in: {user.username}, type: {getattr(user, 'user_type', 'NO TYPE')}")

                if hasattr(user, "user_type"):
                    if user.user_type == "superadmin":
                        return redirect("multiple_gym:superadmin_dashboard")  # ADD NAMESPACE
                    elif user.user_type == "gymadmin":
                        return redirect("multiple_gym:gymadmin_home")  # ADD NAMESPACE
                    elif user.user_type == "member":
                        return redirect("multiple_gym:member_dashboard")  # ADD NAMESPACE
                    elif user.user_type == "trainer":
                        print("Redirecting to trainer_dashboard after login")
                        return redirect("trainer_management:trainer_dashboard")
                    else:
                        print(f"Invalid user type in POST: {user.user_type}")
                        logout(request)
                        messages.error(request, "Invalid user type. Please contact admin.")
                        return redirect("multiple_gym:login")  # ADD NAMESPACE
                else:
                    logout(request)
                    messages.error(request, "User profile incomplete. Please contact admin.")
                    return redirect("multiple_gym:login")  # ADD NAMESPACE
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomLoginForm()

    return render(request, "multiple_gym/login.html", {"form": form})


def logout_view(request):
    print(f"=== LOGOUT VIEW ===")
    logout(request)
    messages.success(request, "Successfully logged out!")
    return redirect("multiple_gym:login")


@login_required
def superadmin_dashboard(request):
    print(f"=== SUPERADMIN DASHBOARD DEBUG ===")
    if request.user.user_type != "superadmin":
        messages.error(request, "Access denied!")
        return redirect("login")

    gyms = Gym.objects.all().order_by("-registration_date")
    total_gyms = gyms.count()
    total_members = Member.objects.count()

    context = {
        "gyms": gyms,
        "total_gyms": total_gyms,
        "total_members": total_members,
    }
    return render(request, "multiple_gym/superadmin_dashboard.html", context)


@login_required
def create_gym(request):
    if request.user.user_type != "superadmin":
        messages.error(request, "Access denied!")
        return redirect("login")

    if request.method == "POST":
        form = GymCreationForm(request.POST)
        if form.is_valid():
            # Create gym
            gym = form.save(commit=False)
            gym.created_by = request.user
            gym.save()

            # Create gym admin user
            admin_user = User.objects.create_user(
                username=form.cleaned_data["admin_username"],
                email=form.cleaned_data["admin_email"],
                password=form.cleaned_data["admin_password"],
                user_type="gymadmin",
                phone=form.cleaned_data.get("admin_phone", ""),
            )

            # Create gym admin and link to gym
            gym_admin = GymAdmin.objects.create(user=admin_user)
            gym_admin.gyms.add(gym)

            messages.success(request, f'Gym "{gym.name}" created successfully!')
            return redirect("superadmin_dashboard")
    else:
        form = GymCreationForm()

    return render(request, "multiple_gym/create_gym.html", {"form": form})


@login_required
def gymadmin_home(request):
    """Redirect gymadmin to their first gym's dashboard"""
    if request.user.user_type != "gymadmin":
        messages.error(request, "Access denied!")
        return redirect("login")

    try:
        gym_admin = GymAdmin.objects.get(user=request.user)
        first_gym = gym_admin.gyms.first()
        if first_gym:
            return redirect("multiple_gym:gymadmin_dashboard", gym_id=first_gym.id)
        else:
            messages.error(request, "No gyms assigned to you yet.")
            return redirect("login")
    except GymAdmin.DoesNotExist:
        messages.error(request, "Gym admin profile not found!")
        return redirect("login")


@login_required
def gymadmin_dashboard(request, gym_id):
    print(f"=== GYMADMIN DASHBOARD DEBUG ===")
    if request.user.user_type != "gymadmin":
        messages.error(request, "Access denied!")
        return redirect("login")

    try:
        gym_admin = GymAdmin.objects.get(user=request.user)
        gym = get_object_or_404(Gym, id=gym_id)

        # Check if this gym belongs to the current admin
        if gym not in gym_admin.gyms.all():
            messages.error(request, "You do not have access to this gym!")
            return redirect("gymadmin_home")

        gyms = gym_admin.gyms.all()
        total_members = sum(g.members.filter(is_active=True).count() for g in gyms)

        context = {
            "gym": gym,  # Current gym
            "gyms": gyms,  # All gyms for this admin
            "total_gyms": gyms.count(),
            "total_members": total_members,
            "gym_id": gym_id,
        }
    except GymAdmin.DoesNotExist:
        messages.error(request, "Gym admin profile not found!")
        return redirect("login")

    return render(request, "multiple_gym/gymadmin_dashboard.html", context)


# views.py
# views.py - Updated view with default password generation


# views.py - Membership wala scene completely hata diya
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import get_user_model
import secrets
import string

User = get_user_model()

@login_required
def add_member(request, gym_id):
    """Add new member - supports both gym admin and trainer access"""
    
    # Check user type permissions
    if request.user.user_type not in ["gymadmin", "trainer"]:
        messages.error(request, "Access denied!")
        return redirect("multiple_gym:login")

    gym = get_object_or_404(Gym, id=gym_id)

    # Permission checks based on user type
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "You do not have access to this gym!")
                return redirect("multiple_gym:gymadmin_dashboard", gym_id=gym.id)
        except GymAdmin.DoesNotExist:
            messages.error(request, "Gym admin profile not found!")
            return redirect("multiple_gym:login")
    
    elif request.user.user_type == "trainer":
        try:
            # Import here to avoid circular imports
            from trainer_management.models import Trainer
            
            trainer = Trainer.objects.get(user=request.user, gym=gym, is_active=True)
            
            # Check if trainer has permission to create members
            if not trainer.permissions.can_create_members:
                messages.error(request, "You don't have permission to create members!")
                return redirect("trainer_management:trainer_dashboard")
                
        except Trainer.DoesNotExist:
            messages.error(request, "Trainer profile not found or not authorized for this gym!")
            return redirect("trainer_management:trainer_dashboard")

    if request.method == "POST":
        form = MemberCreationForm(request.POST, request.FILES)
        if form.is_valid():
            # Check if phone number already exists
            phone = form.cleaned_data.get("phone")
            if phone and Member.objects.filter(phone=phone).exists():
                messages.error(
                    request, f"A member with phone number {phone} already exists!"
                )
                context = {
                    "form": form, 
                    "gym": gym, 
                    "gym_id": gym.id,
                    "user_type": request.user.user_type,
                    "is_trainer": request.user.user_type == "trainer"
                }
                # Use different template based on user type
                template_name = "trainer_management/add_member.html" if request.user.user_type == "trainer" else "multiple_gym/add_member.html"
                return render(request, template_name, context)

            try:
                with transaction.atomic():
                    # Generate password if not provided
                    password = form.cleaned_data.get("password")
                    if not password:
                        password = "".join(
                            secrets.choice(string.ascii_letters + string.digits)
                            for _ in range(8)
                        )

                    # Create member user
                    member_user = User.objects.create_user(
                        username=form.cleaned_data["username"],
                        email=form.cleaned_data["email"],
                        password=password,
                        user_type="member",
                    )

                    member_user.first_name = form.cleaned_data["first_name"]
                    member_user.last_name = form.cleaned_data["last_name"]

                    if hasattr(member_user, "phone"):
                        member_user.phone = form.cleaned_data.get("phone", "")

                    member_user.save()

                    # Create member profile
                    member_data = {
                        "user": member_user,
                        "gym": gym,
                    }

                    # Add phone to member_data if it exists
                    if phone:
                        member_data["phone"] = phone

                    optional_fields = [
                        "date_of_birth",
                        "gender",
                        "blood_group",
                        "alternate_phone",
                        "photo",
                        "address_line1",
                        "address_line2",
                        "city",
                        "state",
                        "pin_code",
                        "medical_conditions",
                        "medications",
                        "previous_injuries",
                        "emergency_contact_name",
                        "emergency_contact_phone",
                        "emergency_contact_relation",
                        "emergency_contact_address",
                        "emergency_contact_name2",
                        "emergency_contact_phone2",
                        "emergency_contact_relation2",
                    ]

                    for field in optional_fields:
                        if hasattr(Member, field) and form.cleaned_data.get(field):
                            member_data[field] = form.cleaned_data[field]

                    member = Member.objects.create(**member_data)

                    # If trainer created the member, auto-assign them
                    if request.user.user_type == "trainer":
                        from trainer_management.models import MemberTrainerAssignment
                        
                        trainer = Trainer.objects.get(user=request.user, gym=gym)
                        
                        # Create automatic assignment
                        MemberTrainerAssignment.objects.create(
                            member=member,
                            trainer=trainer,
                            assignment_type='fitness',  # Default assignment type
                            goals='New member - initial assessment required',
                            notes=f'Auto-assigned when member was created by {trainer.user.get_full_name()}',
                            created_by=request.user
                        )

                    success_msg = (
                        f'Member "{form.cleaned_data["username"]}" added successfully!'
                    )
                    if not form.cleaned_data.get("password"):
                        success_msg += f" Generated password: {password}"
                    
                    # Add trainer-specific message
                    if request.user.user_type == "trainer":
                        success_msg += " Member has been automatically assigned to you."

                    messages.success(request, success_msg)
                    
                    # Redirect based on user type
                    if request.user.user_type == "gymadmin":
                        return redirect("multiple_gym:gym_detail", gym_id=gym.id)
                    else:  # trainer
                        return redirect("trainer_management:trainer_member_list")

            except Exception as e:
                messages.error(request, f"Error creating member: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = MemberCreationForm()

    context = {
        "form": form, 
        "gym": gym, 
        "gym_id": gym.id,
        "user_type": request.user.user_type,
        "is_trainer": request.user.user_type == "trainer",
        "title": "Add New Member"
    }
    
    # Choose template based on user type
    if request.user.user_type == "trainer":
        return render(request, "trainer_management/add_member.html", context)
    else:
        return render(request, "multiple_gym/add_member.html", context)
    
    
@login_required
def gym_detail(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id)

    # Check access permissions - UPDATED to include trainer
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "Access denied!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")
    elif request.user.user_type == "trainer":
        # ADD TRAINER PERMISSION CHECK
        try:
            from trainer_management.models import Trainer  # Import trainer model
            trainer = Trainer.objects.get(user=request.user)
            if trainer.gym.id != gym_id:
                messages.error(request, "Access denied! You can only view your assigned gym.")
                return redirect("trainer_management:trainer_dashboard")
        except Trainer.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")
    elif request.user.user_type != "superadmin":
        messages.error(request, "Access denied!")
        return redirect("login")

    # membership_start_date remove kar diya, ab created_at use kar rahe hain
    members = gym.members.all().order_by("-created_at")

    context = {
        "gym": gym,
        "members": members,
        "active_members": members.filter(is_active=True).count(),
        "total_members": members.count(),
        "gym_id": gym_id,  # Pass gym_id to template
    }
    return render(request, "multiple_gym/gym_detail.html", context)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from datetime import date, timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from datetime import date, timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from datetime import date, timedelta

@login_required
def member_dashboard(request):
    if request.user.user_type != "member":
        messages.error(request, "Access denied!")
        return redirect("multiple_gym:login")
    
    try:
        member = Member.objects.get(user=request.user)
        
        # Get ALL memberships ordered by most recent first
        all_memberships = Membership.objects.filter(member_name=member).order_by("-start_date")
        
        # Get current date
        today = date.today()
        
        # Find the CURRENTLY ACTIVE membership (overlapping with today's date)
        active_membership = all_memberships.filter(
            start_date__lte=today,
            end_date__gte=today,
            is_active=True
        ).first()
        
        # If no active membership found, check if there's any active membership regardless of dates
        if not active_membership:
            active_membership = all_memberships.filter(is_active=True).first()
        
        # Calculate membership status and days remaining
        days_remaining = 0
        membership_status = "No Active Membership"
        
        if active_membership:
            if active_membership.end_date >= today:
                days_remaining = (active_membership.end_date - today).days
                membership_status = "Active"
            else:
                membership_status = "Expired"
                days_remaining = 0
        
        # Create a list with membership data including calculated fields
        memberships_with_data = []
        for membership in all_memberships:
            # Calculate status based on current date
            if membership.start_date <= today <= membership.end_date:
                if membership.is_active:
                    current_status = "active"
                else:
                    current_status = "inactive"
            elif membership.end_date < today:
                current_status = "expired"
            else:
                current_status = "upcoming"
            
            # Calculate payment percentage
            payment_percentage = 0
            if membership.total_amount > 0:
                payment_percentage = (membership.paid_amount / membership.total_amount) * 100
            
            # Calculate days remaining for this membership
            membership_days_remaining = 0
            if membership.end_date >= today:
                membership_days_remaining = (membership.end_date - today).days
            
            # Create a dictionary with all the data we need
            memberships_with_data.append({
                'membership': membership,
                'current_status': current_status,
                'payment_percentage': round(payment_percentage, 1),
                'days_remaining': membership_days_remaining
            })
        
        # Payment calculations
        all_payments = Payment.objects.filter(membership__member_name=member)
        total_paid = sum(p.amount for p in all_payments) if all_payments.exists() else Decimal('0')
        
        # Calculate total due across all memberships with outstanding balances
        total_due = sum(m.remaining_amount for m in all_memberships if m.remaining_amount > 0)
        
        # Recent payments for display (last 10)
        recent_payments = all_payments.order_by('-payment_date')[:10]
        
        # Payment percentage for active membership
        payment_percentage = 0
        if active_membership and active_membership.total_amount > 0:
            payment_percentage = (active_membership.paid_amount / active_membership.total_amount) * 100
        
        # ===== TRAINING SESSIONS DATA =====
        # Initialize all variables with default values first
        todays_sessions = []
        upcoming_sessions = []
        available_sessions = []
        active_sessions_count = 0
        recent_attendance = []
        missed_sessions_list = []
        total_sessions_enrolled = 0
        attended_sessions = 0
        missed_sessions = 0
        attendance_rate = 0
        enrolled_sessions = []
        
        # Try to load session data
        try:
            from trainer_management.models import SessionParticipant, TrainingSession
            
            # Get member's enrolled sessions
            enrolled_sessions = SessionParticipant.objects.filter(
                member=member, 
                is_enrolled=True
            ).select_related('session', 'session__trainer')
            
            # Today's sessions
            todays_sessions = enrolled_sessions.filter(session__session_date=today)
            
            # Upcoming sessions (future dates only, ordered by date)
            upcoming_sessions = enrolled_sessions.filter(
                session__session_date__gt=today
            ).order_by('session__session_date', 'session__start_time')
            
            # Available sessions to join (not enrolled, future dates)
            available_sessions = TrainingSession.objects.filter(
                trainer__gym=member.gym,
                session_date__gte=today,
                status='scheduled'
            ).exclude(
                id__in=enrolled_sessions.values_list('session_id', flat=True)
            )[:5]
            
            # Total active sessions count
            active_sessions_count = enrolled_sessions.filter(
                session__status__in=['scheduled', 'active']
            ).count()
            
            # Recent attendance records (completed sessions only)
            recent_attendance = SessionParticipant.objects.filter(
                member=member,
                attended=True,
                session__session_date__lt=today
            ).select_related(
                'session', 
                'session__trainer'
            ).prefetch_related(
                'session__content_materials'
            ).order_by('-session__session_date')[:15]
            
            # 🔥 FIXED: Missed sessions (enrolled but didn't attend past sessions)
            missed_sessions_list = SessionParticipant.objects.filter(
                member=member,
                is_enrolled=True,  # Must be enrolled
                attended=False,    # But didn't attend
                session__session_date__lt=today  # Past sessions only
            ).select_related(
                'session', 
                'session__trainer'
            ).prefetch_related(
                'session__content_materials'
            ).order_by('-session__session_date')
            
            # Debug: Print missed sessions count
            missed_count = missed_sessions_list.count()
            print(f"DEBUG: Found {missed_count} missed sessions for member {member.user.username}")
            
            # 🔥 FIXED: Attendance statistics - count ALL enrolled sessions with past dates
            all_past_enrolled_sessions = enrolled_sessions.filter(
                session__session_date__lt=today
            )
            
            total_sessions_enrolled = all_past_enrolled_sessions.count()
            attended_sessions = all_past_enrolled_sessions.filter(attended=True).count()
            missed_sessions = all_past_enrolled_sessions.filter(attended=False).count()
            
            print(f"DEBUG: Attendance stats - Total Past: {total_sessions_enrolled}, Attended: {attended_sessions}, Missed: {missed_sessions}")
            
            if total_sessions_enrolled > 0:
                attendance_rate = (attended_sessions / total_sessions_enrolled) * 100
        
        except ImportError:
            # If trainer_management app is not available, use default values
            print("Trainer management app not available - using default session values")
        except Exception as e:
            # Handle any other errors
            print(f"Error loading session data: {e}")
        
        # ===== MEMBERSHIP STATISTICS =====
        total_memberships = all_memberships.count()
        expired_memberships = all_memberships.filter(end_date__lt=today).count()
        active_memberships_count = all_memberships.filter(
            start_date__lte=today,
            end_date__gte=today,
            is_active=True
        ).count()
        
        # ===== PAYMENT SUMMARY =====
        total_payments_made = all_payments.count()
        payment_completion_rate = 0
        
        # Calculate overall payment completion rate across all memberships
        total_membership_amount = sum(m.total_amount for m in all_memberships if m.total_amount > 0)
        total_paid_amount = sum(m.paid_amount for m in all_memberships if m.paid_amount > 0)
        
        if total_membership_amount > 0:
            payment_completion_rate = (total_paid_amount / total_membership_amount) * 100
        
        # Outstanding payments - memberships with remaining balance
        outstanding_payments = all_memberships.filter(
            remaining_amount__gt=0
        ).order_by('-start_date')
        
        # ===== ENHANCED MEMBER STATS =====
        current_weight = getattr(member, 'current_weight', 75)
        target_weight = getattr(member, 'target_weight', 70)
        height = getattr(member, 'height', 170)
        
        # Calculate BMI if height and weight are available
        bmi = 22.5  # Default
        if hasattr(member, 'height') and hasattr(member, 'current_weight'):
            if member.height and member.current_weight:
                height_m = member.height / 100
                bmi = round(member.current_weight / (height_m ** 2), 1)
        
        body_fat_percentage = getattr(member, 'body_fat_percentage', 15)
        
        context = {
            # Member & Gym Info
            "member": member,
            "gym": member.gym,
            "today": today,
            
            # Membership Data
            "active_membership": active_membership,
            "all_memberships": all_memberships,
            "memberships_with_data": memberships_with_data,
            "days_remaining": days_remaining,
            "membership_status": membership_status,
            "total_memberships": total_memberships,
            "expired_memberships": expired_memberships,
            "active_memberships_count": active_memberships_count,
            
            # Payment Data
            "total_paid": total_paid,
            "total_due": total_due,
            "recent_payments": recent_payments,
            "payment_percentage": round(payment_percentage, 1),
            "total_payments_made": total_payments_made,
            "payment_completion_rate": round(payment_completion_rate, 1),
            "outstanding_payments": outstanding_payments,
            
            # Session Data
            "todays_sessions": todays_sessions,
            "upcoming_sessions": upcoming_sessions,
            "available_sessions": available_sessions,
            "active_sessions_count": active_sessions_count,
            "enrolled_sessions": enrolled_sessions,
            
            # Attendance Data
            "recent_attendance": recent_attendance,
            "missed_sessions_list": missed_sessions_list,
            "total_sessions_enrolled": total_sessions_enrolled,
            "attended_sessions": attended_sessions,
            "missed_sessions": missed_sessions,
            "attendance_rate": round(attendance_rate, 1),
            
            # Progress Data
            "current_weight": current_weight,
            "target_weight": target_weight,
            "bmi": bmi,
            "body_fat_percentage": body_fat_percentage,
        }
        
        return render(request, "multiple_gym/member_dashboard.html", context)
        
    except Member.DoesNotExist:
        messages.error(request, "Member profile not found!")
        return redirect("multiple_gym:login")
    except Exception as e:
        print(f"Error in member dashboard: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return redirect("multiple_gym:login")


# Add logout view
@login_required
def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, "Successfully logged out!")
    return redirect("multiple_gym:login")


# Add logout view
@login_required
def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, "Successfully logged out!")
    return redirect("multiple_gym:login")



# MEMBERSHIP PLAN VIEWS
@login_required
def plan_list(request):
    plans = MembershipPlan.objects.all()

    gym_id = None
    gym = None
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            gym = gym_admin.gyms.first()
            if gym:
                gym_id = gym.id
        except GymAdmin.DoesNotExist:
            gym_id = None

    context = {"plans": plans, "gym": gym, "gym_id": gym_id}
    return render(request, "multiple_gym/plan_list.html", context)


@login_required
def create_plan(request):
    gym_id = None
    gym = None
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            gym = gym_admin.gyms.first()
            if gym:
                gym_id = gym.id
        except GymAdmin.DoesNotExist:
            gym_id = None

    if request.method == "POST":
        form = MembershipPlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Membership Plan successfully created!")
            return redirect("plan_list")
    else:
        form = MembershipPlanForm()

    context = {"form": form, "gym": gym, "gym_id": gym_id}
    return render(request, "multiple_gym/create_plan.html", context)


@login_required
def plan_detail(request, pk):
    plan = get_object_or_404(MembershipPlan, pk=pk)

    # Get gym_id for gymadmin menu
    gym_id = None
    gym = None
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            gym = gym_admin.gyms.first()
            if gym:
                gym_id = gym.id
        except GymAdmin.DoesNotExist:
            gym_id = None

    context = {
        "plan": plan,
        "gym": gym,
        "gym_id": gym_id,
    }

    return render(request, "multiple_gym/plan_detail.html", context)


# MEMBERSHIP VIEWS
@login_required
def membership_list(request, gym_id=None):
    gym = None
    
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            
            # If gym_id is provided in URL, use it; otherwise use first gym
            if gym_id:
                gym = get_object_or_404(Gym, id=gym_id)
                # Check if this gym belongs to the current admin
                if gym not in gym_admin.gyms.all():
                    messages.error(request, "You do not have access to this gym!")
                    gym = gym_admin.gyms.first()
                    gym_id = gym.id if gym else None
            else:
                gym = gym_admin.gyms.first()
                gym_id = gym.id if gym else None
            
            if gym:
                # Filter memberships only for this gym admin's gym
                memberships = Membership.objects.filter(
                    member_name__gym=gym
                ).order_by("-start_date")
            else:
                memberships = Membership.objects.none()
                messages.warning(request, "No gyms assigned to you.")
                
        except GymAdmin.DoesNotExist:
            memberships = Membership.objects.none()
            messages.error(request, "Gym admin profile not found!")
            return redirect("login")
            
    elif request.user.user_type == "superadmin":
        # Superadmin can see all memberships
        gym_id_param = gym_id or request.GET.get('gym_id')
        
        if gym_id_param:
            try:
                gym = Gym.objects.get(id=gym_id_param)
                memberships = Membership.objects.filter(
                    member_name__gym=gym
                ).order_by("-start_date")
                gym_id = gym.id
            except Gym.DoesNotExist:
                messages.error(request, "Gym not found!")
                memberships = Membership.objects.all().order_by("-start_date")
                gym_id = None
        else:
            memberships = Membership.objects.all().order_by("-start_date")
            gym_id = None
    else:
        # Other user types shouldn't access this
        messages.error(request, "Access denied!")
        return redirect("login")

    context = {
        "memberships": memberships,
        "gym": gym,
        "gym_id": gym_id,
        "total_memberships": memberships.count(),
        "active_memberships": memberships.filter(membership_status='active').count(),
        "pending_memberships": memberships.filter(payment_status__in=['partial', 'unpaid']).count(),
    }
    return render(request, "multiple_gym/membership_list.html", context)

@login_required
def create_membership(request):
    gym = None
    gym_id = None

    # Debug: Print user type
    print(f"User type: {request.user.user_type}")

    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            gym = gym_admin.gyms.first()  # Get the first gym
            if gym:
                gym_id = gym.id
                print(f"Found gym: {gym.name} (ID: {gym_id})")

                # Debug: Check available members
                members = Member.objects.filter(gym=gym, is_active=True)
                print(f"Available members count: {members.count()}")
                for member in members:
                    print(
                        f"Member: {member.user.username} - Active: {member.is_active}"
                    )
            else:
                print("No gym found for gym admin")
        except GymAdmin.DoesNotExist:
            print("GymAdmin object not found")
            gym = None
    elif request.user.user_type == "superadmin":
        print("User is superadmin")
        # For superadmin, get gym from URL parameters
        gym_id = request.GET.get("gym_id")
        if gym_id:
            try:
                gym = Gym.objects.get(id=gym_id)
                print(f"Superadmin accessing gym: {gym.name}")
            except Gym.DoesNotExist:
                print("Invalid gym_id provided")
                gym = None

    if request.method == "POST":
        form = MembershipForm(request.POST, gym=gym)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create membership
                    membership = form.save(commit=False)
                    membership.total_amount = membership.plan.price

                    # Get payment details from form
                    payment_type = request.POST.get("payment_type", "full")
                    payment_method = request.POST.get("payment_method")
                    payment_notes = request.POST.get("payment_notes", "")

                    if payment_type == "partial":
                        from decimal import Decimal

                        partial_amount = Decimal(
                            str(request.POST.get("partial_amount", 0))
                        )
                        next_payment_date = request.POST.get("next_payment_date")

                        # Validate partial amount
                        if partial_amount <= 0 or partial_amount >= Decimal(
                            str(membership.plan.price)
                        ):

                            messages.error(request, "Invalid partial payment amount!")
                            raise ValueError("Invalid partial amount")

                        membership.paid_amount = partial_amount
                        membership.payment_status = "partial"
                        membership.membership_status = "pending"
                    else:
                        # Full payment
                        membership.paid_amount = membership.plan.price
                        membership.payment_status = "paid"
                        membership.membership_status = "active"

                    membership.save()

                    # Create payment record
                    payment_amount = membership.paid_amount
                    remaining_amount = membership.total_amount - membership.paid_amount

                    payment = Payment.objects.create(
                        membership=membership,
                        amount=payment_amount,
                        payment_type=payment_type,
                        payment_method=payment_method,
                        payment_status="completed",
                        notes=payment_notes,
                        remaining_amount=remaining_amount,
                        created_by=request.user,
                    )

                    # Set next payment reminder for partial payments
                    if payment_type == "partial" and request.POST.get(
                        "next_payment_date"
                    ):
                        from datetime import datetime

                        try:
                            next_date = datetime.strptime(
                                request.POST.get("next_payment_date"), "%Y-%m-%d"
                            ).date()
                            payment.next_payment_reminder = next_date
                            payment.save()
                        except ValueError:
                            pass  # Invalid date format

                    # Success message with payment details
                    if payment_type == "partial":
                        success_msg = (
                            f"Membership created for {membership.member_name.user.username}! "
                            f"Partial payment of ₹{payment_amount} recorded. "
                            f"Remaining amount: ₹{remaining_amount}"
                        )
                        if payment.next_payment_reminder:
                            success_msg += f" (Next payment reminder: {payment.next_payment_reminder})"
                    else:
                        success_msg = (
                            f"Membership created for {membership.member_name.user.username}! "
                            f"Full payment of ₹{payment_amount} recorded."
                        )

                    messages.success(request, success_msg)
                    return redirect("multiple_gym:membership_list")

            except Exception as e:
                messages.error(request, f"Error creating membership: {str(e)}")
                print(f"Error: {e}")
        else:
            messages.error(request, "Please fix the errors below.")
            print(f"Form errors: {form.errors}")  # Debug form errors
    else:
        form = MembershipForm(gym=gym)

    # Check if there are any members available
    if gym:
        member_count = Member.objects.filter(gym=gym, is_active=True).count()
        print(f"Member count for form: {member_count}")
        if member_count == 0:
            messages.warning(
                request,
                f"No active members found in {gym.name}. Please add members first.",
            )
    else:
        print("No gym available - this might be the issue")
        messages.warning(request, "No gym selected. Please contact administrator.")

    # Get all plans for JavaScript price mapping
    plans = MembershipPlan.objects.filter(is_active=True)

    context = {
        "form": form,
        "gym": gym,
        "gym_id": gym_id,
        "plans": plans,  # Add plans for JavaScript
        "title": "Create New Membership",
    }
    return render(request, "multiple_gym/create_membership.html", context)


# Additional view to handle remaining payments
@login_required
def add_payment(request, membership_id):
    """View to add additional payments for partial memberships"""
    membership = get_object_or_404(Membership, id=membership_id)

    # Access control
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if membership.member_name.gym not in gym_admin.gyms.all():
                messages.error(request, "Access denied!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")
    elif request.user.user_type != "superadmin":
        messages.error(request, "Access denied!")
        return redirect("login")

    if request.method == "POST":
        amount = Decimal(str(request.POST.get("amount", 0)))
        payment_method = request.POST.get("payment_method")
        payment_notes = request.POST.get("payment_notes", "")
        next_payment_date = request.POST.get("next_payment_date")

        if amount <= 0 or amount > Decimal(str(membership.remaining_amount)):
            messages.error(request, "Invalid payment amount!")
            return redirect("membership_detail", pk=membership_id)

        try:
            with transaction.atomic():
                # Update membership
                membership.paid_amount += amount
                membership.save()  # This will trigger the save method to update payment_status

                # Create payment record
                payment = Payment.objects.create(
                    membership=membership,
                    amount=amount,
                    payment_type="installment",
                    payment_method=payment_method,
                    payment_status="completed",
                    notes=payment_notes,
                    remaining_amount=membership.remaining_amount,
                    created_by=request.user,
                )

                # Set next payment reminder if provided
                if next_payment_date and membership.remaining_amount > 0:
                    from datetime import datetime

                    try:
                        next_date = datetime.strptime(
                            next_payment_date, "%Y-%m-%d"
                        ).date()
                        payment.next_payment_reminder = next_date
                        payment.save()
                    except ValueError:
                        pass

                if membership.remaining_amount <= 0:
                    messages.success(
                        request,
                        f"Payment of ₹{amount} recorded! Membership is now fully paid.",
                    )
                else:
                    messages.success(
                        request,
                        f"Payment of ₹{amount} recorded! Remaining: ₹{membership.remaining_amount}",
                    )

                return redirect("membership_detail", pk=membership_id)

        except Exception as e:
            messages.error(request, f"Error processing payment: {str(e)}")

    context = {
        "membership": membership,
        "remaining_amount": membership.remaining_amount,
    }
    return render(request, "multiple_gym/add_payment.html", context)


# View to see payment history
@login_required
def payment_history(request, membership_id):
    """View to see all payments for a membership"""
    membership = get_object_or_404(Membership, id=membership_id)

    # Access control
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if membership.member_name.gym not in gym_admin.gyms.all():
                messages.error(request, "Access denied!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")
    elif request.user.user_type == "member":
        # Members can only see their own payment history
        try:
            member = Member.objects.get(user=request.user)
            if membership.member_name != member:
                messages.error(request, "Access denied!")
                return redirect("member_dashboard")
        except Member.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")
    elif request.user.user_type != "superadmin":
        messages.error(request, "Access denied!")
        return redirect("login")

    payments = Payment.objects.filter(membership=membership).order_by("-payment_date")

    context = {
        "membership": membership,
        "payments": payments,
        "total_payments": payments.count(),
        "total_paid": sum(p.amount for p in payments),
    }
    return render(request, "multiple_gym/payment_history.html", context)


# View to get plan price via AJAX (for dynamic price display)
@login_required
def get_plan_price(request, plan_id):
    """AJAX view to get plan price"""
    try:
        plan = MembershipPlan.objects.get(id=plan_id, is_active=True)
        return JsonResponse(
            {
                "success": True,
                "price": float(plan.price),
                "duration": plan.duration_months,
                "name": plan.name,
            }
        )
    except MembershipPlan.DoesNotExist:
        return JsonResponse({"success": False, "error": "Plan not found"})


# View to get pending payments (for dashboard)
@login_required
def pending_payments_view(request):
    """View to see all pending payments across gyms"""
    if request.user.user_type == "superadmin":
        pending_memberships = Membership.objects.filter(
            payment_status__in=["partial", "unpaid"]
        ).order_by("-created_at")
    elif request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            gyms = gym_admin.gyms.all()
            pending_memberships = Membership.objects.filter(
                member_name__gym__in=gyms, payment_status__in=["partial", "unpaid"]
            ).order_by("-created_at")
        except GymAdmin.DoesNotExist:
            pending_memberships = Membership.objects.none()
    else:
        messages.error(request, "Access denied!")
        return redirect("login")

    context = {
        "pending_memberships": pending_memberships,
        "total_pending": pending_memberships.count(),
        "total_pending_amount": sum(m.remaining_amount for m in pending_memberships),
    }
    return render(request, "multiple_gym/pending_payments.html", context)


@login_required
def membership_detail(request, pk):
    membership = get_object_or_404(Membership, pk=pk)

    gym_id = None
    gym = None
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            gym = gym_admin.gyms.first()
            if gym:
                gym_id = gym.id
        except GymAdmin.DoesNotExist:
            gym_id = None

    context = {"membership": membership, "gym": gym, "gym_id": gym_id}
    return render(request, "multiple_gym/membership_detail.html", context)
