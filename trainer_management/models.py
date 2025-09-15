from django.db import models

# Create your models here.
# trainer_management/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import URLValidator
from datetime import date, datetime
from multiple_gym.models import Gym, Member

class Trainer(models.Model):
    """Trainer model - created by gym admins"""
    # Link to User model
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        limit_choices_to={'user_type': 'trainer'}
    )
    
    # Gym association
    gym = models.ForeignKey(
        'multiple_gym.Gym', 
        on_delete=models.CASCADE, 
        related_name='trainers'
    )
    
    # Personal Information
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ]
    
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    phone = models.CharField(max_length=15)
    alternate_phone = models.CharField(max_length=15, blank=True)
    photo = models.ImageField(upload_to='trainer_photos/', blank=True, null=True)
    
    # Address Information
    address_line1 = models.CharField(max_length=100, blank=True)
    address_line2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    pin_code = models.CharField(max_length=6, blank=True)
    
    # Professional Information
    specialization = models.CharField(max_length=200, blank=True, help_text="e.g., Weight Training, Yoga, Cardio")
    certifications = models.TextField(blank=True, help_text="List of certifications")
    experience_years = models.IntegerField(default=0)
    bio = models.TextField(blank=True, help_text="Professional bio/description")
    
    # Salary/Payment Information
    salary_type = models.CharField(max_length=20, choices=[
        ('fixed', 'Fixed Monthly'),
        ('hourly', 'Per Hour'),
        ('session', 'Per Session'),
        ('commission', 'Commission Based')
    ], default='fixed')
    salary_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status and Tracking
    is_active = models.BooleanField(default=True)
    hire_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_trainers'
    )
    
    class Meta:
        verbose_name = "Trainer"
        verbose_name_plural = "Trainers"
        ordering = ['-created_at']
        unique_together = ['user', 'gym']  # One trainer per gym per user
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.gym.name}"
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    @property
    def assigned_members_count(self):
        return self.assigned_members.filter(is_active=True).count()
    
    @property
    def total_sessions_count(self):
        return self.sessions.count()
    
    @property
    def active_sessions_count(self):
        return self.sessions.filter(status='active').count()


class TrainerPermission(models.Model):
    """Permissions for trainers - what they can do"""
    trainer = models.OneToOneField(Trainer, on_delete=models.CASCADE, related_name='permissions')
    
    # Member Management Permissions
    can_create_members = models.BooleanField(default=False, help_text="Can create new members")
    can_edit_members = models.BooleanField(default=False, help_text="Can edit member profiles")
    can_view_all_members = models.BooleanField(default=True, help_text="Can view all gym members")
    
    # Session Management Permissions
    can_create_sessions = models.BooleanField(default=True, help_text="Can create training sessions")
    can_edit_sessions = models.BooleanField(default=True, help_text="Can edit their sessions")
    can_delete_sessions = models.BooleanField(default=False, help_text="Can delete sessions")
    
    # Content Management Permissions
    can_upload_content = models.BooleanField(default=True, help_text="Can upload session content")
    can_manage_assignments = models.BooleanField(default=False, help_text="Can assign/unassign members")
    
    # Reporting Permissions
    can_view_reports = models.BooleanField(default=False, help_text="Can view gym reports")
    can_view_payments = models.BooleanField(default=False, help_text="Can view member payments")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Permissions for {self.trainer.user.username}"


class MemberTrainerAssignment(models.Model):
    """Assignment of members to trainers"""
    member = models.ForeignKey(
        'multiple_gym.Member', 
        on_delete=models.CASCADE, 
        related_name='trainer_assignments'
    )
    trainer = models.ForeignKey(
        Trainer, 
        on_delete=models.CASCADE, 
        related_name='assigned_members'
    )
    
    # Assignment details
    assigned_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True, help_text="Leave blank for ongoing assignment")
    
    # Assignment type and goals
    assignment_type = models.CharField(max_length=50, choices=[
        ('weight_loss', 'Weight Loss'),
        ('muscle_gain', 'Muscle Gain'),
        ('fitness', 'General Fitness'),
        ('strength', 'Strength Training'),
        ('cardio', 'Cardio Training'),
        ('rehabilitation', 'Rehabilitation'),
        ('sport_specific', 'Sport Specific'),
        ('other', 'Other')
    ], default='fitness')
    
    goals = models.TextField(blank=True, help_text="Specific fitness goals")
    notes = models.TextField(blank=True, help_text="Additional notes about assignment")
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        help_text="Gym admin who made the assignment"
    )
    
    class Meta:
        # unique_together = ['member', 'trainer']  # One active assignment per member-trainer pair
        ordering = ['-assigned_date']
    
    def __str__(self):
        return f"{self.member.user.username} assigned to {self.trainer.user.username}"
    
    @property
    def is_ongoing(self):
        """Check if assignment is still active"""
        if not self.is_active:
            return False
        if self.end_date:
            return date.today() <= self.end_date
        return True

# trainer_management/models.py - TrainingSession model update
# trainer_management/models.py - Complete TrainingSession model

import random
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import URLValidator
from datetime import date, datetime
from multiple_gym.models import Gym, Member

class TrainingSession(models.Model):
    """Training sessions created by trainers - COMPLETE VERSION"""
    SESSION_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled')
    ]
    
    SESSION_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('group', 'Group'),
        ('class', 'Class'),
        ('online', 'Online'),
        ('assessment', 'Assessment')
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trainer = models.ForeignKey('Trainer', on_delete=models.CASCADE, related_name='sessions')
    
    # Session Details
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='individual')
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.IntegerField(default=60, help_text="Duration in minutes")    
    location = models.CharField(max_length=200, blank=True, help_text="Room/Area or Online platform")
    max_participants = models.IntegerField(default=1, help_text="Maximum number of participants")
    
    # ZOOM INTEGRATION FIELDS
    is_zoom_session = models.BooleanField(default=False, help_text="Is this a Zoom session?")
    zoom_meeting_id = models.CharField(max_length=50, blank=True, help_text="Zoom Meeting ID")
    zoom_meeting_password = models.CharField(max_length=50, blank=True, help_text="Zoom Meeting Password") 
    zoom_meeting_url = models.URLField(blank=True, help_text="Zoom Meeting Join URL")
    zoom_host_key = models.CharField(max_length=50, blank=True, help_text="Zoom Host Key")
    zoom_recording_enabled = models.BooleanField(default=True, help_text="Enable automatic recording")
    zoom_session_started = models.BooleanField(default=False, help_text="Has Zoom session been started?")
    zoom_session_start_time = models.DateTimeField(null=True, blank=True, help_text="When Zoom session was actually started")
    
    # Status and Progress
    status = models.CharField(max_length=20, choices=SESSION_STATUS_CHOICES, default='scheduled')
    difficulty_level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert')
    ], default='beginner')
    
    # Content and Materials
    workout_plan = models.TextField(blank=True, help_text="Detailed workout plan")
    equipment_needed = models.CharField(max_length=500, blank=True, help_text="Equipment required")
    warm_up_exercises = models.TextField(blank=True)
    main_exercises = models.TextField(blank=True)
    cool_down_exercises = models.TextField(blank=True)
    
    # Session Notes
    pre_session_notes = models.TextField(blank=True, help_text="Notes before session")
    post_session_notes = models.TextField(blank=True, help_text="Notes after session")
    trainer_feedback = models.TextField(blank=True, help_text="Trainer's feedback")
    
    # 🔥 REQUIRED TRACKING FIELDS - Add these missing fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-session_date', '-start_time']
        verbose_name = "Training Session"
        verbose_name_plural = "Training Sessions"
    
    def __str__(self):
        return f"{self.title} - {self.session_date} by {self.trainer.user.username}"
    
    # 🔥 REQUIRED PROPERTIES for Admin - Add these missing properties
    @property
    def is_past(self):
        """Check if session date has passed"""
        return self.session_date < date.today()
    
    @property
    def is_today(self):
        """Check if session is today"""
        return self.session_date == date.today()
    
    @property
    def participants_count(self):
        """Count of enrolled participants"""
        return self.participants.filter(is_enrolled=True).count()
    
    @property
    def available_spots(self):
        """Available spots for enrollment"""
        return max(0, self.max_participants - self.participants_count)
    
    # ZOOM UTILITY METHODS
    def generate_zoom_meeting_id(self):
        """Generate a fake Zoom meeting ID for demo purposes"""
        return f"{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"
    
    def generate_zoom_password(self):
        """Generate a simple password for Zoom meeting"""
        return f"Gym{random.randint(100,999)}"
    
    def get_zoom_web_url(self):
        """Get web version of Zoom URL to avoid app redirect"""
        if self.zoom_meeting_id:
            base_url = "https://zoom.us/wc/join/"
            meeting_id = self.zoom_meeting_id.replace('-', '')
            if self.zoom_meeting_password:
                return f"{base_url}{meeting_id}?pwd={self.zoom_meeting_password}"
            return f"{base_url}{meeting_id}"
        return ""
    
    def setup_zoom_meeting(self):
        """Setup Zoom meeting details when creating online session"""
        if self.session_type == 'online' or self.is_zoom_session:
            if not self.zoom_meeting_id:
                self.zoom_meeting_id = self.generate_zoom_meeting_id()
            if not self.zoom_meeting_password:
                self.zoom_meeting_password = self.generate_zoom_password()
            if not self.zoom_meeting_url:
                self.zoom_meeting_url = f"https://zoom.us/j/{self.zoom_meeting_id.replace('-', '')}"
            self.is_zoom_session = True
            self.save()
    
    @property
    def zoom_participants_notified(self):
        """Check how many participants have been notified"""
        if self.is_zoom_session:
            return self.participants.filter(is_enrolled=True, zoom_notified=True).count()
        return 0

# trainer_management/models.py - SessionParticipant model update

class SessionParticipant(models.Model):
    """Members enrolled in training sessions - UPDATED WITH ZOOM"""
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name='participants')
    member = models.ForeignKey('multiple_gym.Member', on_delete=models.CASCADE, related_name='training_sessions')
    
    # Enrollment details (existing)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_enrolled = models.BooleanField(default=True)
    
    # Attendance (existing)
    attended = models.BooleanField(default=False)
    attendance_marked_at = models.DateTimeField(null=True, blank=True)
    
    # 🆕 ZOOM SPECIFIC FIELDS
    zoom_notified = models.BooleanField(default=False, help_text="Has been notified about Zoom session")
    zoom_notification_sent_at = models.DateTimeField(null=True, blank=True)
    zoom_joined = models.BooleanField(default=False, help_text="Has joined the Zoom session")
    zoom_join_time = models.DateTimeField(null=True, blank=True)
    zoom_leave_time = models.DateTimeField(null=True, blank=True)
    
    # Performance and Feedback (existing fields remain same)
    performance_rating = models.IntegerField(
        null=True, 
        blank=True,
        choices=[(i, f"{i} Star{'s' if i != 1 else ''}") for i in range(1, 6)],
        help_text="Performance rating 1-5 stars"
    )
    member_feedback = models.TextField(blank=True, help_text="Member's feedback about session")
    trainer_notes = models.TextField(blank=True, help_text="Trainer's notes about member's performance")
    
    class Meta:
        unique_together = ['session', 'member']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.member.user.username} in {self.session.title}"
    
    # 🆕 ZOOM UTILITY METHODS
    def notify_zoom_session(self):
        """Mark as notified for Zoom session"""
        if self.session.is_zoom_session and not self.zoom_notified:
            self.zoom_notified = True
            self.zoom_notification_sent_at = timezone.now()
            self.save()
            return True
        return False
    
    def join_zoom_session(self):
        """Mark as joined Zoom session"""
        if self.session.is_zoom_session:
            self.zoom_joined = True
            self.zoom_join_time = timezone.now()
            if not self.attended:
                self.attended = True  # Auto mark attendance when joining Zoom
            self.save()
            return True
        return False
    


class SessionContent(models.Model):
    """Content materials for training sessions"""
    CONTENT_TYPE_CHOICES = [
        ('pdf', 'PDF Document'),
        ('video', 'Video'),
        ('youtube', 'YouTube Video'),
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('link', 'External Link'),
        ('text', 'Text Content')
    ]
    
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name='content_materials')
    
    # Content Details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    
    # File uploads
    file = models.FileField(upload_to='session_content/', null=True, blank=True)
    
    # URLs and Links
    youtube_url = models.URLField(blank=True, help_text="YouTube video URL")
    external_url = models.URLField(blank=True, help_text="External link URL")
    
    # Text content
    text_content = models.TextField(blank=True, help_text="Text-based content")
    
    # Metadata
    file_size = models.BigIntegerField(null=True, blank=True, help_text="File size in bytes")
    duration = models.CharField(max_length=20, blank=True, help_text="Duration for video/audio content")
    
    # Organization
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_required = models.BooleanField(default=False, help_text="Required content for session")
    
    # Access Control
    is_public = models.BooleanField(default=False, help_text="Visible to all members or only participants")
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='uploaded_content'
    )
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Session Content"
        verbose_name_plural = "Session Content"
    
    def __str__(self):
        return f"{self.title} ({self.content_type}) - {self.session.title}"
    
    @property
    def file_size_formatted(self):
        """Human readable file size"""
        if not self.file_size:
            return "Unknown"
        
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"


class SessionAttendance(models.Model):
    """Track attendance for training sessions"""
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name='attendance_records')
    member = models.ForeignKey('multiple_gym.Member', on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    
    # Attendance Details
    marked_present = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    
    # Performance Metrics
    exercises_completed = models.TextField(blank=True, help_text="List of completed exercises")
    sets_completed = models.IntegerField(default=0)
    reps_completed = models.IntegerField(default=0)
    weight_lifted = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Health Metrics
    pre_workout_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    post_workout_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    heart_rate_max = models.IntegerField(null=True, blank=True)
    heart_rate_avg = models.IntegerField(null=True, blank=True)
    
    # Session Feedback
    member_energy_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High')
    ], blank=True)
    
    member_satisfaction = models.IntegerField(
        null=True, 
        blank=True,
        choices=[(i, f"{i} Star{'s' if i != 1 else ''}") for i in range(1, 6)]
    )
    
    # Notes
    trainer_notes = models.TextField(blank=True)
    member_notes = models.TextField(blank=True)
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['session', 'member']
        ordering = ['-created_at']
    
    def __str__(self):
        status = "Present" if self.marked_present else "Absent"
        return f"{self.member.user.username} - {self.session.title} ({status})"
    
    @property
    def session_duration(self):
        """Calculate actual session duration"""
        if self.check_in_time and self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            return duration.total_seconds() / 60  # Return in minutes
        return None