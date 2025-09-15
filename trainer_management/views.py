from django.shortcuts import render

# Create your views here.
# trainer_management/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import date, datetime, timedelta
from decimal import Decimal
import secrets
import string

# Import models
from .models import (
    Trainer, TrainerPermission, MemberTrainerAssignment,
    TrainingSession, SessionParticipant, SessionContent, SessionAttendance
)
from multiple_gym.models import Gym, GymAdmin, Member

User = get_user_model()


# TRAINER MANAGEMENT VIEWS (for Gym Admins)

@login_required
def trainer_list(request, gym_id):
    """List all trainers for a gym"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    gym = get_object_or_404(Gym, id=gym_id)

    # Check access permissions for gymadmin
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "You do not have access to this gym!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")

    # Get trainers for this gym
    trainers = Trainer.objects.filter(gym=gym, is_active=True).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        trainers = trainers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(specialization__icontains=search_query)
        )

    # Calculate statistics
    total_trainers = trainers.count()
    total_assigned_members = sum(t.assigned_members_count for t in trainers)
    total_sessions = sum(t.total_sessions_count for t in trainers)

    context = {
        'gym': gym,
        'gym_id': gym_id,
        'trainers': trainers,
        'search_query': search_query,
        'total_trainers': total_trainers,
        'total_assigned_members': total_assigned_members,
        'total_sessions': total_sessions,
    }

    return render(request, 'trainer_management/trainer_list.html', context)

# trainer_management/views.py - Fixed add_trainer function

@login_required
def add_trainer(request, gym_id):
    """Add new trainer - FIXED VERSION"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    gym = get_object_or_404(Gym, id=gym_id)

    # Check access permissions
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "You do not have access to this gym!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                username = request.POST.get('username')
                email = request.POST.get('email')
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                phone = request.POST.get('phone')
                
                # Check if username already exists
                if User.objects.filter(username=username).exists():
                    messages.error(request, f"Username '{username}' already exists!")
                    return render(request, 'trainer_management/add_trainer.html', {
                        'gym': gym,
                        'gym_id': gym_id,
                    })
                
                # Check if email already exists
                if User.objects.filter(email=email).exists():
                    messages.error(request, f"Email '{email}' already exists!")
                    return render(request, 'trainer_management/add_trainer.html', {
                        'gym': gym,
                        'gym_id': gym_id,
                    })

                # Generate password if not provided
                password = request.POST.get('password')
                if not password:
                    password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))

                # 🔥 FIXED: Create trainer user with correct user_type
                trainer_user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    user_type='trainer',  # 🔥 यहाँ था problem - missing trainer user_type
                    first_name=first_name,
                    last_name=last_name,
                )
                
                # Add phone to User model if it has phone field
                if hasattr(trainer_user, 'phone'):
                    trainer_user.phone = phone
                    trainer_user.save()

                print(f"✅ Created trainer user: {trainer_user.username} with user_type: {trainer_user.user_type}")

                # Create trainer profile
                trainer = Trainer.objects.create(
                    user=trainer_user,
                    gym=gym,
                    phone=phone,
                    alternate_phone=request.POST.get('alternate_phone', ''),
                    date_of_birth=request.POST.get('date_of_birth') if request.POST.get('date_of_birth') else None,
                    gender=request.POST.get('gender', ''),
                    address_line1=request.POST.get('address_line1', ''),
                    address_line2=request.POST.get('address_line2', ''),
                    city=request.POST.get('city', ''),
                    state=request.POST.get('state', ''),
                    pin_code=request.POST.get('pin_code', ''),
                    specialization=request.POST.get('specialization', ''),
                    certifications=request.POST.get('certifications', ''),
                    experience_years=int(request.POST.get('experience_years', 0)),
                    bio=request.POST.get('bio', ''),
                    salary_type=request.POST.get('salary_type', 'fixed'),
                    salary_amount=Decimal(str(request.POST.get('salary_amount', 0))),
                    hire_date=request.POST.get('hire_date') if request.POST.get('hire_date') else date.today(),
                    created_by=request.user
                )

                print(f"✅ Created trainer profile: {trainer.id}")

                # Create default permissions
                permissions = TrainerPermission.objects.create(
                    trainer=trainer,
                    can_create_members=request.POST.get('can_create_members') == 'on',
                    can_edit_members=request.POST.get('can_edit_members') == 'on',
                    can_view_all_members=request.POST.get('can_view_all_members', 'on') == 'on',
                    can_create_sessions=request.POST.get('can_create_sessions', 'on') == 'on',
                    can_edit_sessions=request.POST.get('can_edit_sessions', 'on') == 'on',
                    can_delete_sessions=request.POST.get('can_delete_sessions') == 'on',
                    can_upload_content=request.POST.get('can_upload_content', 'on') == 'on',
                    can_manage_assignments=request.POST.get('can_manage_assignments') == 'on',
                    can_view_reports=request.POST.get('can_view_reports') == 'on',
                    can_view_payments=request.POST.get('can_view_payments') == 'on'
                )

                print(f"✅ Created trainer permissions: {permissions.id}")

                success_msg = f'Trainer "{trainer.user.get_full_name()}" added successfully!'
                if not request.POST.get('password'):
                    success_msg += f' Generated password: {password}'

                messages.success(request, success_msg)
                return redirect('trainer_management:trainer_list', gym_id=gym_id)

        except Exception as e:
            print(f"❌ Error creating trainer: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f"Error creating trainer: {str(e)}")

    context = {
        'gym': gym,
        'gym_id': gym_id,
    }

    return render(request, 'trainer_management/add_trainer.html', context)

@login_required
def trainer_detail(request, gym_id, trainer_id):
    """View trainer details"""
    gym = get_object_or_404(Gym, id=gym_id)
    trainer = get_object_or_404(Trainer, id=trainer_id, gym=gym)

    # Check access permissions
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
        # Trainers can only view their own profile
        if trainer.user != request.user:
            messages.error(request, "Access denied!")
            return redirect("trainer_dashboard")
    elif request.user.user_type not in ["superadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    # Get assigned members
    assigned_members = trainer.assigned_members.filter(is_active=True).order_by('-assigned_date')
    
    # Get recent sessions
    recent_sessions = trainer.sessions.all().order_by('-session_date', '-start_time')[:10]
    
    # Get statistics
    total_sessions = trainer.sessions.count()
    completed_sessions = trainer.sessions.filter(status='completed').count()
    upcoming_sessions = trainer.sessions.filter(
        session_date__gte=date.today(),
        status__in=['scheduled', 'active']
    ).count()

    context = {
        'gym': gym,
        'gym_id': gym_id,
        'trainer': trainer,
        'assigned_members': assigned_members,
        'recent_sessions': recent_sessions,
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'upcoming_sessions': upcoming_sessions,
    }

    return render(request, 'trainer_management/trainer_detail.html', context)


@login_required
def assign_members_to_trainer(request, gym_id, trainer_id):
    """Assign/Unassign members to trainer"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    gym = get_object_or_404(Gym, id=gym_id)
    trainer = get_object_or_404(Trainer, id=trainer_id, gym=gym)

    # Check access permissions
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "Access denied!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")

    if request.method == 'POST':
        selected_members = request.POST.getlist('members')
        assignment_type = request.POST.get('assignment_type', 'fitness')
        goals = request.POST.get('goals', '')
        notes = request.POST.get('notes', '')

        try:
            with transaction.atomic():
                # Only clear existing assignments between THIS trainer and selected members
                existing_assignments = MemberTrainerAssignment.objects.filter(
                    member_id__in=selected_members,
                    trainer=trainer,  # Only for this specific trainer
                    is_active=True
                )
                existing_assignments.update(is_active=False)

                # Create new assignments
                new_assignments_count = 0
                for member_id in selected_members:
                    member = get_object_or_404(Member, id=member_id, gym=gym)
                    
                    # Check if this exact assignment already exists
                    existing = MemberTrainerAssignment.objects.filter(
                        member=member,
                        trainer=trainer,
                        is_active=True
                    ).exists()
                    
                    if not existing:
                        MemberTrainerAssignment.objects.create(
                            member=member,
                            trainer=trainer,
                            assignment_type=assignment_type,
                            goals=goals,
                            notes=notes,
                            created_by=request.user
                        )
                        new_assignments_count += 1

                messages.success(request, f'{new_assignments_count} new members assigned to {trainer.user.get_full_name()}')
                return redirect('trainer_management:trainer_detail', gym_id=gym_id, trainer_id=trainer_id)

        except Exception as e:
            messages.error(request, f"Error assigning members: {str(e)}")

    # Get available members and already assigned members to THIS trainer
    all_members = Member.objects.filter(gym=gym, is_active=True)
    assigned_member_ids = trainer.assigned_members.filter(is_active=True).values_list('member_id', flat=True)

    context = {
        'gym': gym,
        'gym_id': gym_id,
        'trainer': trainer,
        'all_members': all_members,
        'assigned_member_ids': list(assigned_member_ids),
    }

    return render(request, 'trainer_management/assign_members.html', context)

@login_required
def trainer_permissions(request, gym_id, trainer_id):
    """Manage trainer permissions"""
    if request.user.user_type not in ["superadmin", "gymadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    gym = get_object_or_404(Gym, id=gym_id)
    trainer = get_object_or_404(Trainer, id=trainer_id, gym=gym)

    # Check access permissions
    if request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if gym not in gym_admin.gyms.all():
                messages.error(request, "Access denied!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")

    # Get or create permissions
    permissions, created = TrainerPermission.objects.get_or_create(trainer=trainer)

    if request.method == 'POST':
        try:
            # Update permissions
            permissions.can_create_members = request.POST.get('can_create_members') == 'on'
            permissions.can_edit_members = request.POST.get('can_edit_members') == 'on'
            permissions.can_view_all_members = request.POST.get('can_view_all_members') == 'on'
            permissions.can_create_sessions = request.POST.get('can_create_sessions') == 'on'
            permissions.can_edit_sessions = request.POST.get('can_edit_sessions') == 'on'
            permissions.can_delete_sessions = request.POST.get('can_delete_sessions') == 'on'
            permissions.can_upload_content = request.POST.get('can_upload_content') == 'on'
            permissions.can_manage_assignments = request.POST.get('can_manage_assignments') == 'on'
            permissions.can_view_reports = request.POST.get('can_view_reports') == 'on'
            permissions.can_view_payments = request.POST.get('can_view_payments') == 'on'
            permissions.save()

            messages.success(request, f'Permissions updated for {trainer.user.get_full_name()}')
            return redirect('trainer_management:trainer_detail', gym_id=gym_id, trainer_id=trainer_id)

        except Exception as e:
            messages.error(request, f"Error updating permissions: {str(e)}")

    context = {
        'gym': gym,
        'gym_id': gym_id,
        'trainer': trainer,
        'permissions': permissions,
    }

    return render(request, 'trainer_management/trainer_permissions.html', context)


# TRAINER DASHBOARD VIEWS

# trainer_management/views.py - Complete trainer_dashboard with full Zoom integration

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import date, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


@login_required
def trainer_dashboard(request):
    """Main trainer dashboard with Zoom integration"""
    if request.user.user_type != "trainer":
        messages.error(request, "Access denied!")
        return redirect("multiple_gym:login")
    
    try:
        trainer = Trainer.objects.get(user=request.user, is_active=True)
    except Trainer.DoesNotExist:
        messages.error(request, "Trainer profile not found!")
        return redirect("login")
    
    # Date calculations
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    month_start = today.replace(day=1)
    next_week_end = today + timedelta(days=7)
    
    # Get today's sessions
    today_sessions = trainer.sessions.filter(
        session_date=today,
        status__in=['scheduled', 'active']
    ).prefetch_related('participants__member__user').order_by('start_time')
    
    # Get upcoming sessions (next 7 days, excluding today)
    upcoming_sessions = trainer.sessions.filter(
        session_date__range=[today + timedelta(days=1), next_week_end],
        status__in=['scheduled', 'active']
    ).prefetch_related('participants__member__user').order_by('session_date', 'start_time')
    
    # Get assigned members
    assigned_members = trainer.assigned_members.filter(
        is_active=True
    ).select_related('member__user').order_by('-assigned_date')
    
    # Basic statistics
    total_assigned_members = assigned_members.count()
    
    total_sessions_today = today_sessions.count()
    
    total_sessions_this_week = trainer.sessions.filter(
        session_date__range=[week_start, week_end]
    ).count()
    
    completed_sessions_this_month = trainer.sessions.filter(
        session_date__range=[month_start, today],
        status='completed'
    ).count()
    
    # Zoom specific statistics
    today_zoom_sessions = today_sessions.filter(is_zoom_session=True).count()
    
    upcoming_zoom_sessions = upcoming_sessions.filter(is_zoom_session=True).count()
    
    active_sessions = trainer.sessions.filter(
        status='active',
        session_date=today
    ).count()
    
    # Context for template
    context = {
        'trainer': trainer,
        
        # Session data
        'today_sessions': today_sessions,
        'upcoming_sessions': upcoming_sessions,
        'assigned_members': assigned_members[:10],  # First 10 for sidebar
        
        # Basic stats (template required)
        'total_assigned_members': total_assigned_members,
        'total_sessions_today': total_sessions_today,
        'total_sessions_this_week': total_sessions_this_week,
        'completed_sessions_this_month': completed_sessions_this_month,
        
        # Zoom stats (template required)
        'today_zoom_sessions': today_zoom_sessions,
        'upcoming_zoom_sessions': upcoming_zoom_sessions,
        'active_sessions': active_sessions,
    }
    
    return render(request, 'trainer_management/trainer_dashboard.html', context)
# SESSION MANAGEMENT VIEWS

@login_required
def trainer_member_list(request):
    """List of members assigned to the trainer"""
    if request.user.user_type != "trainer":
        messages.error(request, "Access denied!")
        return redirect("login")

    try:
        trainer = Trainer.objects.get(user=request.user, is_active=True)
    except Trainer.DoesNotExist:
        messages.error(request, "Trainer profile not found!")
        return redirect("login")

    # Get assigned members
    assignments = trainer.assigned_members.filter(is_active=True).select_related(
        'member__user', 'member__gym'
    ).order_by('-assigned_date')

    context = {
        'trainer': trainer,
        'assignments': assignments,
        'gym': trainer.gym,
    }

    return render(request, 'trainer_management/member_list.html', context)

@login_required
def session_list(request):
    """List trainer's sessions"""
    if request.user.user_type != "trainer":
        messages.error(request, "Access denied!")
        return redirect("login")

    try:
        trainer = Trainer.objects.get(user=request.user, is_active=True)
    except Trainer.DoesNotExist:
        messages.error(request, "Trainer profile not found!")
        return redirect("login")

    # Get sessions
    sessions = trainer.sessions.all().order_by('-session_date', '-start_time')

    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        sessions = sessions.filter(status=status_filter)

    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        sessions = sessions.filter(session_date__gte=date_from)
    if date_to:
        sessions = sessions.filter(session_date__lte=date_to)

    # Search
    search_query = request.GET.get('search')
    if search_query:
        sessions = sessions.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    context = {
        'trainer': trainer,
        'sessions': sessions,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
    }

    return render(request, 'trainer_management/session_list.html', context)



# trainer_management/views.py - FIXED create_session view

@login_required
def create_session(request):
    """Create new training session - UPDATED WITH ZOOM INTEGRATION"""
    if request.user.user_type != "trainer":
        messages.error(request, "Access denied!")
        return redirect("multiple_gym:login")

    try:
        trainer = Trainer.objects.get(user=request.user, is_active=True)
        permissions = trainer.permissions
        
        if not permissions.can_create_sessions:
            messages.error(request, "You don't have permission to create sessions!")
            return redirect("trainer_management:trainer_dashboard")
            
    except Trainer.DoesNotExist:
        messages.error(request, "Trainer profile not found!")
        return redirect("multiple_gym:login")

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Validate required fields first
                title = request.POST.get('title', '').strip()
                session_type = request.POST.get('session_type', '').strip()
                session_date = request.POST.get('session_date', '').strip()
                start_time = request.POST.get('start_time', '').strip()
                end_time = request.POST.get('end_time', '').strip()

                if not title:
                    messages.error(request, "Session title is required!")
                    raise ValueError("Missing title")
                
                if not session_type:
                    messages.error(request, "Session type is required!")
                    raise ValueError("Missing session type")
                
                if not session_date:
                    messages.error(request, "Session date is required!")
                    raise ValueError("Missing session date")

                if not start_time:
                    messages.error(request, "Start time is required!")
                    raise ValueError("Missing start time")

                if not end_time:
                    messages.error(request, "End time is required!")
                    raise ValueError("Missing end time")

                # Safe integer conversion for duration_minutes
                duration_raw = request.POST.get('duration_minutes', '').strip()
                if duration_raw:
                    try:
                        duration_minutes = int(float(duration_raw))
                        if duration_minutes <= 0:
                            duration_minutes = 60
                    except (ValueError, TypeError):
                        duration_minutes = 60
                else:
                    duration_minutes = 60

                # Safe integer conversion for max_participants
                max_participants_raw = request.POST.get('max_participants', '').strip()
                if max_participants_raw:
                    try:
                        max_participants = int(float(max_participants_raw))
                        if max_participants <= 0:
                            max_participants = 1
                    except (ValueError, TypeError):
                        max_participants = 1
                else:
                    max_participants = 1

                # Create session
                session = TrainingSession.objects.create(
                    title=title,
                    description=request.POST.get('description', '').strip(),
                    trainer=trainer,
                    session_type=session_type,
                    session_date=session_date,
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=duration_minutes,
                    location=request.POST.get('location', '').strip(),
                    max_participants=max_participants,
                    difficulty_level=request.POST.get('difficulty_level', 'beginner').strip(),
                    workout_plan=request.POST.get('workout_plan', '').strip(),
                    equipment_needed=request.POST.get('equipment_needed', '').strip(),
                    warm_up_exercises=request.POST.get('warm_up_exercises', '').strip(),
                    main_exercises=request.POST.get('main_exercises', '').strip(),
                    cool_down_exercises=request.POST.get('cool_down_exercises', '').strip(),
                    pre_session_notes=request.POST.get('pre_session_notes', '').strip(),
                    
                    # 🔥 ZOOM FIELDS - ADD THESE MISSING LINES
                    is_zoom_session=request.POST.get('is_zoom_session') == 'on',
                    zoom_recording_enabled=request.POST.get('zoom_recording_enabled', 'on') == 'on',
                )

                print(f"Session created: {session.title}, type: {session.session_type}, is_zoom: {session.is_zoom_session}")

                # 🔥 AUTO SETUP ZOOM FOR ONLINE SESSIONS - ADD THIS LOGIC
                if session.session_type == 'online' or session.is_zoom_session:
                    session.setup_zoom_meeting()
                    print(f"✅ Zoom setup complete: ID={session.zoom_meeting_id}, Password={session.zoom_meeting_password}")

                # Add participants if selected
                selected_members = request.POST.getlist('participants')
                participants_added = 0
                
                for member_id in selected_members:
                    member_id = member_id.strip()
                    if member_id:
                        try:
                            member_id_int = int(member_id)
                            member = Member.objects.get(id=member_id_int, gym=trainer.gym)
                            SessionParticipant.objects.create(
                                session=session,
                                member=member
                            )
                            participants_added += 1
                            print(f"Participant added: {member.user.get_full_name()}")
                        except (ValueError, TypeError):
                            continue
                        except Member.DoesNotExist:
                            continue

                success_msg = f'Session "{session.title}" created successfully!'
                # 🔥 ADD ZOOM SUCCESS MESSAGE
                if session.is_zoom_session:
                    success_msg += f' Zoom meeting setup complete (ID: {session.zoom_meeting_id})!'
                if participants_added > 0:
                    success_msg += f' {participants_added} participant(s) added.'
                
                messages.success(request, success_msg)
                return redirect('trainer_management:session_detail', session_id=session.id)

        except ValueError:
            # Validation errors already added to messages
            pass
        except Exception as e:
            print(f"❌ Error creating session: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f"Error creating session: {str(e)}")

    # Get assigned members for participant selection
    assigned_members = trainer.assigned_members.filter(is_active=True)

    context = {
        'trainer': trainer,
        'assigned_members': assigned_members,
        'gym': trainer.gym,
    }

    return render(request, 'trainer_management/create_session.html', context)
# trainer_management/views.py mein add karo:

@login_required
def add_participant(request, session_id):
    """Add participant to training session"""
    if request.user.user_type != "trainer":
        messages.error(request, "Access denied!")
        return redirect("multiple_gym:login")

    try:
        trainer = Trainer.objects.get(user=request.user, is_active=True)
        session = get_object_or_404(TrainingSession, id=session_id, trainer=trainer)
        
    except Trainer.DoesNotExist:
        messages.error(request, "Trainer profile not found!")
        return redirect("multiple_gym:login")

    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        if member_id:
            try:
                member = get_object_or_404(Member, id=member_id, gym=trainer.gym)
                
                # Check if participant already exists
                if SessionParticipant.objects.filter(session=session, member=member).exists():
                    messages.warning(request, f'{member.user.get_full_name()} is already enrolled in this session.')
                else:
                    # Check session capacity
                    if session.participants_count >= session.max_participants:
                        messages.error(request, 'Session is already at maximum capacity.')
                    else:
                        SessionParticipant.objects.create(
                            session=session,
                            member=member
                        )
                        messages.success(request, f'{member.user.get_full_name()} added to session successfully!')
                        
            except Member.DoesNotExist:
                messages.error(request, 'Selected member not found.')
        else:
            messages.error(request, 'Please select a member.')
    
    return redirect('trainer_management:session_detail', session_id=session_id)

@login_required
def session_detail(request, session_id):
    """View session details"""
    session = get_object_or_404(TrainingSession, id=session_id)

    # Check access permissions
    if request.user.user_type == "trainer":
        trainer = get_object_or_404(Trainer, user=request.user)
        if session.trainer != trainer:
            messages.error(request, "Access denied!")
            return redirect("trainer_dashboard")
    elif request.user.user_type == "gymadmin":
        try:
            gym_admin = GymAdmin.objects.get(user=request.user)
            if session.trainer.gym not in gym_admin.gyms.all():
                messages.error(request, "Access denied!")
                return redirect("gymadmin_home")
        except GymAdmin.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")
    elif request.user.user_type == "member":
        try:
            member = Member.objects.get(user=request.user)
            if not session.participants.filter(member=member, is_enrolled=True).exists():
                messages.error(request, "Access denied!")
                return redirect("member_dashboard")
        except Member.DoesNotExist:
            messages.error(request, "Access denied!")
            return redirect("login")
    elif request.user.user_type != "superadmin":
        messages.error(request, "Access denied!")
        return redirect("login")

    # Get session participants
    participants = session.participants.filter(is_enrolled=True).order_by('enrolled_at')
    
    # Get session content
    content_materials = session.content_materials.all().order_by('order', '-created_at')
    
    # Get attendance records if session is completed
    attendance_records = []
    if session.status == 'completed':
        attendance_records = session.attendance_records.all().order_by('member__user__first_name')

    context = {
        'session': session,
        'participants': participants,
        'content_materials': content_materials,
        'attendance_records': attendance_records,
        'can_edit': request.user.user_type in ['trainer', 'gymadmin', 'superadmin'],
    }

    return render(request, 'trainer_management/session_detail.html', context)

@login_required
def add_session_content(request, session_id):
    """Add content to training session - FIXED VERSION"""
    session = get_object_or_404(TrainingSession, id=session_id)

    # Check permissions
    if request.user.user_type == "trainer":
        try:
            trainer = Trainer.objects.get(user=request.user, is_active=True)
            if session.trainer != trainer:
                messages.error(request, "You can only add content to your own sessions!")
                return redirect("trainer_management:trainer_dashboard")
            
            # Check if trainer has upload permissions
            if not trainer.permissions.can_upload_content:
                messages.error(request, "You don't have permission to upload content!")
                return redirect("trainer_management:trainer_dashboard")
                
        except Trainer.DoesNotExist:
            messages.error(request, "Trainer profile not found!")
            return redirect("multiple_gym:login")
            
    elif request.user.user_type not in ["gymadmin", "superadmin"]:
        messages.error(request, "Access denied!")
        return redirect("multiple_gym:login")

    if request.method == 'POST':
        try:
            # Get basic form data
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            content_type = request.POST.get('content_type', '').strip()
            
            # Validate required fields
            if not title:
                messages.error(request, "Content title is required!")
                raise ValueError("Missing title")
                
            if not content_type:
                messages.error(request, "Content type is required!")
                raise ValueError("Missing content type")
            
            # Safe integer conversion for order
            order_raw = request.POST.get('order', '0').strip()
            try:
                order = int(order_raw) if order_raw else 0
            except (ValueError, TypeError):
                order = 0
            
            # Create content object
            content = SessionContent.objects.create(
                session=session,
                title=title,
                description=description,
                content_type=content_type,
                order=order,
                is_required=request.POST.get('is_required') == 'on',
                is_public=request.POST.get('is_public') == 'on',
                uploaded_by=request.user
            )

            # Handle different content types
            if content_type in ['pdf', 'video', 'image', 'audio']:
                if 'file' in request.FILES and request.FILES['file']:
                    uploaded_file = request.FILES['file']
                    
                    # Basic file size validation (50MB limit)
                    if uploaded_file.size > 50 * 1024 * 1024:
                        content.delete()  # Clean up created content
                        messages.error(request, "File size must be less than 50MB!")
                        raise ValueError("File too large")
                    
                    content.file = uploaded_file
                    content.file_size = uploaded_file.size
                else:
                    content.delete()  # Clean up created content
                    messages.error(request, f"File is required for {content_type} content!")
                    raise ValueError("Missing file")
                
            elif content_type == 'youtube':
                youtube_url = request.POST.get('youtube_url', '').strip()
                if not youtube_url:
                    content.delete()
                    messages.error(request, "YouTube URL is required!")
                    raise ValueError("Missing YouTube URL")
                
                # Basic YouTube URL validation
                import re
                youtube_regex = re.compile(
                    r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
                    r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
                )
                if not youtube_regex.match(youtube_url):
                    content.delete()
                    messages.error(request, "Please enter a valid YouTube URL!")
                    raise ValueError("Invalid YouTube URL")
                
                content.youtube_url = youtube_url
                content.duration = request.POST.get('duration', '').strip()
                
            elif content_type == 'link':
                external_url = request.POST.get('external_url', '').strip()
                if not external_url:
                    content.delete()
                    messages.error(request, "External URL is required!")
                    raise ValueError("Missing external URL")
                
                content.external_url = external_url
                
            elif content_type == 'text':
                text_content = request.POST.get('text_content', '').strip()
                if not text_content:
                    content.delete()
                    messages.error(request, "Text content is required!")
                    raise ValueError("Missing text content")
                
                content.text_content = text_content
            
            else:
                content.delete()
                messages.error(request, "Invalid content type selected!")
                raise ValueError("Invalid content type")

            # Save the content with all data
            content.save()
            
            # Success message
            success_msg = f'Content "{content.title}" ({content.get_content_type_display()}) added successfully!'
            messages.success(request, success_msg)
            
            return redirect('trainer_management:session_detail', session_id=session_id)

        except ValueError:
            # Validation errors already added to messages
            pass
        except Exception as e:
            print(f"❌ Error adding content: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f"Error adding content: {str(e)}")

    # GET request - show form
    context = {
        'session': session,
    }

    return render(request, 'trainer_management/add_session_content.html', context)

@login_required
def mark_attendance(request, session_id):
    """Mark attendance for session participants"""
    session = get_object_or_404(TrainingSession, id=session_id)

    # Check permissions - only trainer or gym admin can mark attendance
    if request.user.user_type == "trainer":
        trainer = get_object_or_404(Trainer, user=request.user)
        if session.trainer != trainer:
            messages.error(request, "Access denied!")
            return redirect("trainer_dashboard")
    elif request.user.user_type not in ["gymadmin", "superadmin"]:
        messages.error(request, "Access denied!")
        return redirect("login")

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Process attendance for each participant
                for participant in session.participants.filter(is_enrolled=True):
                    member = participant.member
                    present_key = f'present_{member.id}'
                    
                    # Get or create attendance record
                    attendance, created = SessionAttendance.objects.get_or_create(
                        session=session,
                        member=member,
                        trainer=session.trainer,
                        defaults={'marked_present': False}
                    )
                    
                    # Update attendance
                    was_present = request.POST.get(present_key) == 'on'
                    attendance.marked_present = was_present
                    
                    if was_present:
                        if not attendance.check_in_time:
                            attendance.check_in_time = timezone.now()
                        
                        # Optional performance data
                        attendance.exercises_completed = request.POST.get(f'exercises_{member.id}', '')
                        attendance.sets_completed = int(request.POST.get(f'sets_{member.id}', 0) or 0)
                        attendance.reps_completed = int(request.POST.get(f'reps_{member.id}', 0) or 0)
                        
                        weight_lifted = request.POST.get(f'weight_{member.id}')
                        if weight_lifted:
                            attendance.weight_lifted = Decimal(str(weight_lifted))
                        
                        attendance.member_energy_level = request.POST.get(f'energy_{member.id}', '')
                        attendance.trainer_notes = request.POST.get(f'notes_{member.id}', '')
                        
                        satisfaction = request.POST.get(f'satisfaction_{member.id}')
                        if satisfaction:
                            attendance.member_satisfaction = int(satisfaction)
                    
                    attendance.save()
                    
                    # Update session participant attendance
                    participant.attended = was_present
                    participant.attendance_marked_at = timezone.now()
                    participant.save()

                # Update session status if not already completed
                if session.status != 'completed':
                    session.status = 'completed'
                    session.post_session_notes = request.POST.get('session_notes', '')
                    session.save()

                messages.success(request, 'Attendance marked successfully!')
                return redirect('trainer_management:session_detail', session_id=session_id)

        except Exception as e:
            messages.error(request, f"Error marking attendance: {str(e)}")

    # Get participants with existing attendance data
    participants_data = []
    for participant in session.participants.filter(is_enrolled=True):
        try:
            attendance = SessionAttendance.objects.get(
                session=session,
                member=participant.member
            )
        except SessionAttendance.DoesNotExist:
            attendance = None
            
        participants_data.append({
            'participant': participant,
            'member': participant.member,
            'attendance': attendance
        })

    context = {
        'session': session,
        'participants_data': participants_data,
    }

    return render(request, 'trainer_management/mark_attendance.html', context)


# AJAX VIEWS

@login_required
def get_member_assignments(request, member_id):
    """AJAX view to get member's trainer assignments"""
    member = get_object_or_404(Member, id=member_id)
    
    assignments = MemberTrainerAssignment.objects.filter(
        member=member,
        is_active=True
    ).select_related('trainer__user')
    
    data = []
    for assignment in assignments:
        data.append({
            'trainer_id': assignment.trainer.id,
            'trainer_name': assignment.trainer.user.get_full_name(),
            'assignment_type': assignment.get_assignment_type_display(),
            'assigned_date': assignment.assigned_date.strftime('%Y-%m-%d'),
            'goals': assignment.goals
        })
    
    return JsonResponse({'assignments': data})


@login_required
def session_calendar_data(request):
    """AJAX view to get session data for calendar"""
    if request.user.user_type != "trainer":
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        trainer = Trainer.objects.get(user=request.user)
    except Trainer.DoesNotExist:
        return JsonResponse({'error': 'Trainer not found'}, status=404)
    
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    sessions = trainer.sessions.filter(
        session_date__range=[start_date, end_date]
    ).select_related('trainer')
    
    events = []
    for session in sessions:
        color = {
            'scheduled': '#007bff',
            'active': '#28a745',
            'completed': '#6c757d',
            'cancelled': '#dc3545',
            'rescheduled': '#ffc107'
        }.get(session.status, '#007bff')
        
        events.append({
            'id': session.id,
            'title': session.title,
            'start': f"{session.session_date}T{session.start_time}",
            'end': f"{session.session_date}T{session.end_time}",
            'backgroundColor': color,
            'borderColor': color,
            'url': f'/trainer/session/{session.id}/',
            'extendedProps': {
                'status': session.status,
                'participants': session.participants_count,
                'location': session.location
            }
        })
    
    return JsonResponse(events, safe=False)



# trainer_management/views.py - FIXED login redirects

import json
import random
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Trainer, TrainingSession

# 🔥 FIXED join_zoom_meeting view with correct redirects
@login_required
def join_zoom_meeting(request, session_id):
    """Handle joining Zoom meeting - FIXED VERSION"""
    if request.user.user_type != "trainer":
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        trainer = Trainer.objects.get(user=request.user, is_active=True)
        session = get_object_or_404(TrainingSession, id=session_id, trainer=trainer)
    except Trainer.DoesNotExist:
        return JsonResponse({'error': 'Trainer not found'}, status=404)
    
    if not session.is_zoom_session:
        return JsonResponse({'error': 'Not a Zoom session'}, status=400)
    
    # Mark session as started if not already
    if not session.zoom_session_started:
        session.status = 'active'
        session.zoom_session_started = True
        session.zoom_session_start_time = timezone.now()
        session.save()
    
    # Return JSON response with Zoom URLs
    return JsonResponse({
        'success': True,
        'web_url': session.get_zoom_web_url(),
        'join_url': session.zoom_meeting_url,
        'meeting_id': session.zoom_meeting_id,
        'password': session.zoom_meeting_password,
        'message': 'Redirecting to Zoom meeting...'
    })


# 🔥 TEST VIEW for debugging - NO LOGIN REQUIRED
def test_zoom_data(request, session_id):
    """Test view to check Zoom data - NO AUTH NEEDED"""
    try:
        session = TrainingSession.objects.get(id=session_id)
        
        # Auto setup zoom if not setup
        if session.session_type == 'online' and not session.is_zoom_session:
            session.setup_zoom_meeting()
        
        test_data = {
            'session_id': session.id,
            'title': session.title,
            'session_type': session.session_type,
            'is_zoom_session': session.is_zoom_session,
            'zoom_meeting_id': session.zoom_meeting_id,
            'zoom_password': session.zoom_meeting_password,
            'zoom_url': session.zoom_meeting_url,
            'web_url': session.get_zoom_web_url() if session.get_zoom_web_url() else 'No web URL',
            'participants_count': session.participants_count,
            'status': session.status,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Test data retrieved successfully',
            'data': test_data
        }, json_dumps_params={'indent': 2})
        
    except TrainingSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)
    except Exception as e:
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


# 🔥 COMPLETE start_zoom_session view with proper redirects
@login_required
def start_zoom_session(request, session_id):
    """Start Zoom session - AJAX view"""
    if request.user.user_type != "trainer":
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        trainer = Trainer.objects.get(user=request.user, is_active=True)
        session = get_object_or_404(TrainingSession, id=session_id, trainer=trainer)
    except Trainer.DoesNotExist:
        return JsonResponse({'error': 'Trainer not found'}, status=404)
    
    if request.method == 'POST':
        try:
            # Setup Zoom meeting if not already done
            if not session.is_zoom_session or not session.zoom_meeting_id:
                session.setup_zoom_meeting()
            
            # Update session status
            session.status = 'active'
            session.zoom_session_started = True
            session.zoom_session_start_time = timezone.now()
            session.save()
            
            # Get Zoom meeting details
            zoom_data = {
                'meeting_id': session.zoom_meeting_id,
                'password': session.zoom_meeting_password,
                'web_url': session.get_zoom_web_url(),
                'join_url': session.zoom_meeting_url,
                'participants_count': session.participants_count,
                'recording_enabled': session.zoom_recording_enabled
            }
            
            return JsonResponse({
                'success': True,
                'message': 'Zoom session started successfully!',
                'session_status': session.status,
                'zoom_data': zoom_data
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


# 🔥 COMPLETE get_zoom_session_data view
@login_required
def get_zoom_session_data(request, session_id):
    """Get Zoom session data for modal - AJAX view"""
    if request.user.user_type != "trainer":
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        trainer = Trainer.objects.get(user=request.user, is_active=True)
        session = get_object_or_404(TrainingSession, id=session_id, trainer=trainer)
    except Trainer.DoesNotExist:
        return JsonResponse({'error': 'Trainer not found'}, status=404)
    
    # Setup Zoom meeting if needed
    if session.session_type == 'online' and not session.is_zoom_session:
        session.setup_zoom_meeting()
    
    # Get participants data
    participants_data = []
    for participant in session.participants.filter(is_enrolled=True):
        participants_data.append({
            'id': participant.member.id,
            'name': participant.member.user.get_full_name(),
            'email': participant.member.user.email,
            'phone': getattr(participant.member, 'phone', ''),
            'notified': participant.zoom_notified,
            'joined': participant.zoom_joined,
            'status': 'joined' if participant.zoom_joined else 'notified' if participant.zoom_notified else 'pending'
        })
    
    zoom_data = {
        'session': {
            'id': session.id,
            'title': session.title,
            'date': session.session_date.strftime('%Y-%m-%d'),
            'start_time': session.start_time.strftime('%H:%M'),
            'duration': session.duration_minutes,
            'status': session.status,
            'is_zoom_session': session.is_zoom_session
        },
        'zoom': {
            'meeting_id': session.zoom_meeting_id,
            'password': session.zoom_meeting_password,
            'web_url': session.get_zoom_web_url(),
            'join_url': session.zoom_meeting_url,
            'recording_enabled': session.zoom_recording_enabled,
            'session_started': session.zoom_session_started
        },
        'participants': participants_data,
        'stats': {
            'total_participants': len(participants_data),
            'notified_count': sum(1 for p in participants_data if p['notified']),
            'joined_count': sum(1 for p in participants_data if p['joined'])
        }
    }
    
    return JsonResponse(zoom_data)


# 🔥 COMPLETE notify_zoom_participants view
@login_required  
def notify_zoom_participants(request, session_id):
    """Send Zoom notifications to participants - AJAX view"""
    if request.user.user_type != "trainer":
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        trainer = Trainer.objects.get(user=request.user, is_active=True)
        session = get_object_or_404(TrainingSession, id=session_id, trainer=trainer)
    except Trainer.DoesNotExist:
        return JsonResponse({'error': 'Trainer not found'}, status=404)
    
    if request.method == 'POST':
        try:
            notified_count = 0
            participants = session.participants.filter(is_enrolled=True, zoom_notified=False)
            
            for participant in participants:
                # Here you would send actual email/SMS notification
                # For now, we'll just mark as notified
                if participant.notify_zoom_session():
                    notified_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'Notifications sent to {notified_count} participant(s)!',
                'notified_count': notified_count,
                'total_participants': session.participants.filter(is_enrolled=True).count()
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)



# trainer_management/views.py - ADD these regular session management views

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Trainer, TrainingSession

# Regular session management views (non-Zoom)

@login_required
def start_session(request, session_id):
    """Start regular session (non-Zoom) - AJAX view"""
    if request.user.user_type != "trainer":
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        trainer = Trainer.objects.get(user=request.user, is_active=True)
        session = get_object_or_404(TrainingSession, id=session_id, trainer=trainer)
    except Trainer.DoesNotExist:
        return JsonResponse({'error': 'Trainer not found'}, status=404)
    
    if request.method == 'POST':
        try:
            # Check if session can be started
            if session.status != 'scheduled':
                return JsonResponse({'error': f'Session is already {session.status}'}, status=400)
            
            # Update session status
            session.status = 'active'
            session.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Session "{session.title}" started successfully!',
                'session_status': session.status,
                'session_id': session.id
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def complete_session(request, session_id):
    """Complete session - AJAX view"""
    if request.user.user_type != "trainer":
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        trainer = Trainer.objects.get(user=request.user, is_active=True)
        session = get_object_or_404(TrainingSession, id=session_id, trainer=trainer)
    except Trainer.DoesNotExist:
        return JsonResponse({'error': 'Trainer not found'}, status=404)
    
    if request.method == 'POST':
        try:
            # Check if session can be completed
            if session.status not in ['active', 'scheduled']:
                return JsonResponse({'error': f'Cannot complete session with status: {session.status}'}, status=400)
            
            # Update session status
            session.status = 'completed'
            
            # Add completion notes if provided
            session_notes = request.POST.get('session_notes', '')
            if session_notes:
                session.post_session_notes = session_notes
            
            session.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Session "{session.title}" completed successfully!',
                'session_status': session.status,
                'session_id': session.id
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def cancel_session(request, session_id):
    """Cancel session - AJAX view"""
    if request.user.user_type != "trainer":
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        trainer = Trainer.objects.get(user=request.user, is_active=True)
        session = get_object_or_404(TrainingSession, id=session_id, trainer=trainer)
    except Trainer.DoesNotExist:
        return JsonResponse({'error': 'Trainer not found'}, status=404)
    
    if request.method == 'POST':
        try:
            # Check if session can be cancelled
            if session.status in ['completed', 'cancelled']:
                return JsonResponse({'error': f'Cannot cancel session with status: {session.status}'}, status=400)
            
            # Update session status
            session.status = 'cancelled'
            
            # Add cancellation notes if provided
            cancel_reason = request.POST.get('cancel_reason', 'Cancelled by trainer')
            session.post_session_notes = f"Cancelled: {cancel_reason}"
            
            session.save()
            
            # Here you could also notify participants about cancellation
            
            return JsonResponse({
                'success': True,
                'message': f'Session "{session.title}" cancelled successfully!',
                'session_status': session.status,
                'session_id': session.id
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


# Utility function to get session status
@login_required
def get_session_status(request, session_id):
    """Get current session status - AJAX view"""
    if request.user.user_type != "trainer":
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        trainer = Trainer.objects.get(user=request.user, is_active=True)
        session = get_object_or_404(TrainingSession, id=session_id, trainer=trainer)
    except Trainer.DoesNotExist:
        return JsonResponse({'error': 'Trainer not found'}, status=404)
    
    return JsonResponse({
        'success': True,
        'session_id': session.id,
        'title': session.title,
        'status': session.status,
        'is_zoom_session': session.is_zoom_session,
        'participants_count': session.participants_count,
        'date': session.session_date.strftime('%Y-%m-%d'),
        'start_time': session.start_time.strftime('%H:%M'),
        'end_time': session.end_time.strftime('%H:%M'),
    })