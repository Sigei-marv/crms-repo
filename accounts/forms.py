from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User

class CustomUserCreationForm(UserCreationForm):
    """
    Form for creating new users in the Savanna County Recruitment System
    Includes all fields needed for the different roles (Initiator, Chief Officer, etc.)
    """
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address',
            'autocomplete': 'email'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    
    national_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter National ID (7-8 digits)'
        }),
        help_text="Kenya National ID Number (7-8 digits)"
    )
    
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number (e.g., +254712345678)'
        }),
        help_text="Phone number in format: +254XXXXXXXXX"
    )
    
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        help_text="Select your role in the recruitment process"
    )
    
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter department (e.g., Health)'
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
            'autocomplete': 'new-password'
        })
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'autocomplete': 'new-password'
        })
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'national_id', 
                 'phone_number', 'role', 'department', 'password1', 'password2')
    
    def clean_email(self):
        """Validate that email is unique"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email
    
    def clean_national_id(self):
        """Validate that national ID is unique and properly formatted"""
        national_id = self.cleaned_data.get('national_id')
        
        # Check if national ID already exists
        if national_id and User.objects.filter(national_id=national_id).exists():
            raise ValidationError('A user with this National ID already exists.')
        
        
        if national_id and not national_id.isdigit():
            raise ValidationError('National ID must contain only digits.')
        
        if national_id and (len(national_id) < 7 or len(national_id) > 8):
            raise ValidationError('National ID must be 7 or 8 digits long.')
        
        return national_id
    
    def clean_phone_number(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone_number')
        
        
        if phone:
           
            phone = phone.replace(' ', '').replace('-', '')
            
           
            if not (phone.startswith('+254') or phone.startswith('254') or phone.startswith('07') or phone.startswith('01')):
                raise ValidationError('Phone number must be in Kenyan format (e.g., +254712345678, 0712345678)')
            
           
            digits_only = ''.join(filter(str.isdigit, phone))
            if len(digits_only) < 9 or len(digits_only) > 12:
                raise ValidationError('Phone number must have between 9 and 12 digits')
        
        return phone
    
    def save(self, commit=True):
        """Save the user with additional processing"""
        user = super().save(commit=False)
        # Set username as email (required by Django)
        user.username = self.cleaned_data['email']
        
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form that uses email instead of username
    """
    
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autocomplete': 'email',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    error_messages = {
        'invalid_login': 'Please enter a correct email and password. Note that both fields may be case-sensitive.',
        'inactive': 'This account is inactive. Please contact the administrator.',
    }
    
    def clean(self):
        """Override clean to use email as username"""
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if email and password:
            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)
        
        return self.cleaned_data


class UserProfileForm(forms.ModelForm):
    """
    Form for updating user profile information
    """
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number'
        })
    )
    
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number', 'profile_picture')
    
    def clean_phone_number(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone_number')
        
        if phone:
          
            phone = phone.replace(' ', '').replace('-', '')
            
           
            if not (phone.startswith('+254') or phone.startswith('254') or phone.startswith('07') or phone.startswith('01')):
                raise ValidationError('Phone number must be in Kenyan format')
        
        return phone