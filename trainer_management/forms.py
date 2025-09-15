
# trainer_management/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from .models import (
    Trainer, TrainerPermission, MemberTrainerAssignment,
    TrainingSession, SessionContent, SessionAttendance
)
from multiple_gym.models import Member

User = get_user_model()

class TrainerCreationForm(forms.ModelForm):
    """Form for creating new trainer"""
    # User fields
    username = forms.CharField(
        max_length=150,
        help_text="Username for trainer login"
    )
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Leave blank to auto-generate password"
    )
    
    # Trainer specific fields
    phone = forms.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    
    class Meta:
        model = Trainer
        fields = [
            'date_of_birth', 'gender', 'phone', 'alternate_phone',
            'address_line1', 'address_line2', 'city', 'state', 'pin_code',
            'specialization', 'certifications', 'experience_years', 'bio',
            'salary_type', 'salary_amount', 'hire_date'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
            'certifications': forms.Textarea(attrs={'rows': 3}),
            'salary_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'experience_years': forms.NumberInput(attrs={'min': '0'}),
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class TrainerPermissionForm(forms.ModelForm):
    """Form for managing trainer permissions"""
    class Meta:
        model = TrainerPermission
        fields = [
            'can_create_members', 'can_edit_members', 'can_view_all_members',
            'can_create_sessions', 'can_edit_sessions', 'can_delete_sessions',
            'can_upload_content', 'can_manage_assignments',
            'can_view_reports', 'can_view_payments'
        ]
        widgets = {
            'can_create_members': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_edit_members': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_all_members': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_create_sessions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_edit_sessions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_delete_sessions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_upload_content': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_assignments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_reports': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_payments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MemberAssignmentForm(forms.ModelForm):
    """Form for assigning members to trainers"""
    members = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Select members to assign to this trainer"
    )
    
    class Meta:
        model = MemberTrainerAssignment
        fields = ['assignment_type', 'goals', 'notes']
        widgets = {
            'goals': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        gym = kwargs.pop('gym', None)
        super().__init__(*args, **kwargs)
        
        if gym:
            self.fields['members'].queryset = Member.objects.filter(
                gym=gym, is_active=True
            ).order_by('user__first_name', 'user__last_name')



# trainer_management/forms.py - Create this new file

from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta, date
from .models import TrainingSession, SessionParticipant
from multiple_gym.models import Member

class TrainingSessionForm(forms.ModelForm):
    """Form for creating/editing training sessions with Zoom integration"""
    
    # Zoom specific fields
    is_zoom_session = forms.BooleanField(
        required=False,
        label="Create as Zoom session",
        help_text="Enable Zoom meeting integration"
    )
    
    zoom_recording_enabled = forms.BooleanField(
        required=False,
        initial=True,
        label="Enable automatic recording",
        help_text="Record Zoom session automatically"
    )
    
    participants = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select members for this session (optional)"
    )
    
    class Meta:
        model = TrainingSession
        fields = [
            'title', 'description', 'session_type', 'session_date',
            'start_time', 'end_time', 'duration_minutes', 'location',
            'max_participants', 'difficulty_level', 'workout_plan',
            'equipment_needed', 'warm_up_exercises', 'main_exercises',
            'cool_down_exercises', 'pre_session_notes',
            'is_zoom_session', 'zoom_recording_enabled'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter session title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of the session'
            }),
            'session_type': forms.Select(attrs={'class': 'form-control'}),
            'session_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time', 
                'class': 'form-control'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '15', 
                'max': '480',
                'value': '60'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Room number or area'
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1', 
                'max': '50',
                'value': '1'
            }),
            'difficulty_level': forms.Select(attrs={'class': 'form-control'}),
            'workout_plan': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detailed workout plan'
            }),
            'equipment_needed': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Dumbbells, Treadmill, Yoga Mat'
            }),
            'warm_up_exercises': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Warm-up routine'
            }),
            'main_exercises': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Main workout exercises'
            }),
            'cool_down_exercises': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Cool-down routine'
            }),
            'pre_session_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any special notes or instructions'
            }),
        }

    def __init__(self, *args, **kwargs):
        trainer = kwargs.pop('trainer', None)
        super().__init__(*args, **kwargs)
        
        # Set minimum date to today
        self.fields['session_date'].widget.attrs['min'] = date.today().isoformat()
        
        if trainer:
            # Only show trainer's assigned members
            self.fields['participants'].queryset = Member.objects.filter(
                trainer_assignments__trainer=trainer,
                trainer_assignments__is_active=True,
                is_active=True
            ).distinct().order_by('user__first_name', 'user__last_name')
        else:
            self.fields['participants'].queryset = Member.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        session_date = cleaned_data.get('session_date')
        session_type = cleaned_data.get('session_type')
        
        # Validate session date is not in the past
        if session_date and session_date < date.today():
            raise ValidationError("Session date cannot be in the past.")
        
        # Validate start and end times
        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError("End time must be after start time.")
            
            # Calculate duration automatically
            start_datetime = datetime.combine(session_date or date.today(), start_time)
            end_datetime = datetime.combine(session_date or date.today(), end_time)
            duration = (end_datetime - start_datetime).total_seconds() / 60
            
            if duration < 15:
                raise ValidationError("Session duration must be at least 15 minutes.")
            if duration > 480:  # 8 hours
                raise ValidationError("Session duration cannot exceed 8 hours.")
                
            cleaned_data['duration_minutes'] = int(duration)
        
        # Auto-enable Zoom for online sessions
        if session_type == 'online':
            cleaned_data['is_zoom_session'] = True
            if not cleaned_data.get('location'):
                cleaned_data['location'] = 'Online - Zoom Meeting'
        
        return cleaned_data

    def save(self, commit=True):
        session = super().save(commit=commit)
        
        if commit:
            # Setup Zoom meeting if needed
            if session.session_type == 'online' or session.is_zoom_session:
                session.setup_zoom_meeting()
            
            # Add selected participants
            participants_data = self.cleaned_data.get('participants', [])
            for member in participants_data:
                SessionParticipant.objects.get_or_create(
                    session=session,
                    member=member,
                    defaults={'is_enrolled': True}
                )
        
        return session


class SessionParticipantForm(forms.ModelForm):
    """Form for managing session participants"""
    
    class Meta:
        model = SessionParticipant
        fields = ['member', 'is_enrolled']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session', None)
        trainer = kwargs.pop('trainer', None)
        super().__init__(*args, **kwargs)
        
        if trainer:
            # Only show trainer's assigned members who aren't already in this session
            existing_participants = []
            if session:
                existing_participants = session.participants.values_list('member_id', flat=True)
            
            self.fields['member'].queryset = Member.objects.filter(
                trainer_assignments__trainer=trainer,
                trainer_assignments__is_active=True,
                is_active=True
            ).exclude(id__in=existing_participants).distinct().order_by(
                'user__first_name', 'user__last_name'
            )
        else:
            self.fields['member'].queryset = Member.objects.none()


class ZoomSessionManagementForm(forms.Form):
    """Form for managing Zoom session settings"""
    
    action = forms.ChoiceField(
        choices=[
            ('notify', 'Send Notifications'),
            ('start', 'Start Session'),
            ('join', 'Join Meeting'),
            ('end', 'End Session'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    recording_enabled = forms.BooleanField(
        required=False,
        initial=True,
        label="Enable Recording"
    )
    
    participant_ids = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Comma-separated participant IDs"
    )
    
    session_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Session notes or feedback'
        }),
        label="Session Notes"
    )
    

class SessionContentForm(forms.ModelForm):
    """Form for adding content to training sessions"""
    class Meta:
        model = SessionContent
        fields = [
            'title', 'description', 'content_type', 'file',
            'youtube_url', 'external_url', 'text_content',
            'duration', 'order', 'is_required', 'is_public'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'text_content': forms.Textarea(attrs={'rows': 5}),
            'order': forms.NumberInput(attrs={'min': '0'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'duration': forms.TextInput(attrs={'placeholder': 'e.g., 10:30 or 5 minutes'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        file = cleaned_data.get('file')
        youtube_url = cleaned_data.get('youtube_url')
        external_url = cleaned_data.get('external_url')
        text_content = cleaned_data.get('text_content')
        
        # Validate based on content type
        if content_type in ['pdf', 'video', 'image', 'audio']:
            if not file:
                raise forms.ValidationError(f"File is required for {content_type} content.")
        elif content_type == 'youtube':
            if not youtube_url:
                raise forms.ValidationError("YouTube URL is required for YouTube content.")
            # Basic YouTube URL validation
            import re
            youtube_regex = re.compile(
                r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
                r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
            )
            if not youtube_regex.match(youtube_url):
                raise forms.ValidationError("Please enter a valid YouTube URL.")
        elif content_type == 'link':
            if not external_url:
                raise forms.ValidationError("External URL is required for link content.")
        elif content_type == 'text':
            if not text_content:
                raise forms.ValidationError("Text content is required for text content type.")
        
        return cleaned_data


class AttendanceForm(forms.Form):
    """Form for marking session attendance"""
    session_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Session Notes",
        help_text="General notes about the session"
    )

    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)
        
        if session:
            # Add fields for each participant
            participants = session.participants.filter(is_enrolled=True)
            
            for participant in participants:
                member = participant.member
                member_id = member.id
                
                # Attendance checkbox
                self.fields[f'present_{member_id}'] = forms.BooleanField(
                    required=False,
                    label=f"Present - {member.user.get_full_name()}",
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                )
                
                # Performance fields
                self.fields[f'exercises_{member_id}'] = forms.CharField(
                    required=False,
                    label="Exercises Completed",
                    widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
                )
                
                self.fields[f'sets_{member_id}'] = forms.IntegerField(
                    required=False,
                    label="Sets",
                    widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': '0'})
                )
                
                self.fields[f'reps_{member_id}'] = forms.IntegerField(
                    required=False,
                    label="Reps",
                    widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': '0'})
                )
                
                self.fields[f'weight_{member_id}'] = forms.DecimalField(
                    required=False,
                    label="Weight (kg)",
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control form-control-sm', 
                        'step': '0.5', 
                        'min': '0'
                    })
                )
                
                self.fields[f'energy_{member_id}'] = forms.ChoiceField(
                    required=False,
                    label="Energy Level",
                    choices=[('', 'Select')] + [
                        ('low', 'Low'),
                        ('medium', 'Medium'),
                        ('high', 'High'),
                        ('very_high', 'Very High')
                    ],
                    widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
                )
                
                self.fields[f'satisfaction_{member_id}'] = forms.ChoiceField(
                    required=False,
                    label="Satisfaction",
                    choices=[('', 'Rate')] + [(i, f"{i} Star{'s' if i != 1 else ''}") for i in range(1, 6)],
                    widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
                )
                
                self.fields[f'notes_{member_id}'] = forms.CharField(
                    required=False,
                    label="Trainer Notes",
                    widget=forms.Textarea(attrs={
                        'class': 'form-control', 
                        'rows': '2',
                        'placeholder': 'Notes about member performance...'
                    })
                )