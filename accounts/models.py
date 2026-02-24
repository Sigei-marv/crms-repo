from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid

class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User Model for Savanna County Recruitment System
    Extends Django's AbstractUser to add additional fields
    """
    # Use email as username
    username = None
    email = models.EmailField('email address', unique=True)
    
    # Personal Information
    national_id = models.CharField(
        max_length=20, 
        unique=True,
        validators=[RegexValidator(r'^\d{7,8}$', 'Enter a valid National ID (7-8 digits)')],
        help_text="Kenya National ID Number"
    )
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number')],
        help_text="Phone number in format: +254XXXXXXXXX"
    )
    
    # Role and Department
    ROLE_CHOICES = [
        ('INITIATOR', 'Initiator (Dr. Amani - Health Director)'),
        ('CHIEF_OFFICER', 'Chief Officer - Health (Madam Joy)'),
        ('COUNTY_SECRETARY', 'County Secretary (Mr. Kiplagat)'),
        ('CPSB_BOARD', 'CPSB Board Member'),
        ('CPSB_SECRETARIAT', 'CPSB Secretariat'),
        ('HR_SECRETARIAT', 'HR Secretariat'),
        ('HR_ADMIN', 'HR Administrator'),
        ('PANELIST', 'Interview Panelist'),
        ('PAYROLL_OFFICER', 'Payroll Officer'),
    ]
    
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='INITIATOR')
    department = models.CharField(max_length=100, blank=True, default='Health')
    
    # Additional fields
    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Audit fields
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Fix: Add related_name to avoid clashes with auth.User
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    
    # Use email as the unique identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['national_id', 'phone_number', 'first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        permissions = [
            ('can_approve_requisitions', 'Can approve requisitions'),
            ('can_endorse_requisitions', 'Can endorse requisitions'),
            ('can_board_approve', 'Can approve at board level'),
            ('can_shortlist', 'Can shortlist candidates'),
            ('can_interview', 'Can conduct interviews'),
            ('can_verify_documents', 'Can verify candidate documents'),
            ('can_generate_offers', 'Can generate appointment letters'),
            ('can_export_payroll', 'Can export payroll data'),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.get_role_display()}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_role_group(self):
        """Get the Django group name for this user's role"""
        role_to_group = {
            'INITIATOR': 'Initiators',
            'CHIEF_OFFICER': 'Chief Officers',
            'COUNTY_SECRETARY': 'County Secretaries',
            'CPSB_BOARD': 'CPSB Board',
            'CPSB_SECRETARIAT': 'CPSB Secretariat',
            'HR_SECRETARIAT': 'HR Secretariat',
            'HR_ADMIN': 'HR Administrators',
            'PANELIST': 'Panelists',
            'PAYROLL_OFFICER': 'Payroll Officers',
        }
        return role_to_group.get(self.role, 'Applicants')
    
    def save(self, *args, **kwargs):
        """Override save to ensure employee_id is set"""
        if not self.employee_id:
            # Generate employee ID: SAV + year + random number
            import random
            year = timezone.now().year
            random_num = random.randint(1000, 9999)
            self.employee_id = f"SAV{year}{random_num}"
        super().save(*args, **kwargs)


class UserActivityLog(models.Model):
    """Track user activities for audit purposes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'User Activity Log'
        verbose_name_plural = 'User Activity Logs'
    
    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.timestamp}"