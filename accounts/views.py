from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import Group
from django.views.decorators.cache import never_cache
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from .models import User, UserActivityLog
from core.decorators import role_required

def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            group_name = user.get_role_group()
            group, created = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
            
            UserActivityLog.objects.create(
                user=user,
                action='USER_REGISTERED',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                data={'role': user.role}
            )
            
            messages.success(request, 'Registration successful! Please login.')
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@never_cache
def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user)
                
                UserActivityLog.objects.create(
                    user=user,
                    action='USER_LOGIN',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                )
                
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                
                if user.role == 'INITIATOR':
                    return redirect('requisitions:create')
                elif user.role == 'CHIEF_OFFICER':
                    return redirect('requisitions:pending_approvals')
                elif user.role == 'COUNTY_SECRETARY':
                    return redirect('requisitions:pending_endorsements')
                elif user.role == 'CPSB_BOARD':
                    return redirect('requisitions:board_approvals')
                elif user.role == 'HR_SECRETARIAT':
                    return redirect('candidates:shortlist')
                else:
                    return redirect('core:dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    """User logout view"""
    # Log the activity
    UserActivityLog.objects.create(
        user=request.user,
        action='USER_LOGOUT',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('accounts:login')

@login_required
def profile_view(request):
    """View and edit user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            
            # Log the activity
            UserActivityLog.objects.create(
                user=request.user,
                action='PROFILE_UPDATED',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {
        'form': form,
        'user': request.user
    })

@login_required
@role_required(['HR_ADMIN', 'CPSB_SECRETARIAT'])
def user_management_view(request):
    """Admin view for managing users"""
    users = User.objects.all().order_by('-date_joined')
    
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    search = request.GET.get('search')
    if search:
        users = users.filter(
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(email__icontains=search) |
            models.Q(national_id__icontains=search)
        )
    
    context = {
        'users': users,
        'role_choices': User.ROLE_CHOICES,
        'current_role': role_filter,
        'search_term': search,
    }
    
    return render(request, 'accounts/user_management.html', context)

@login_required
@role_required(['HR_ADMIN', 'CPSB_SECRETARIAT'])
def toggle_user_active(request, user_id):
    """Activate/deactivate user"""
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            # Don't allow deactivating yourself
            if user == request.user:
                messages.error(request, 'You cannot deactivate your own account!')
            else:
                user.is_active = not user.is_active
                user.save()
                
                action = 'activated' if user.is_active else 'deactivated'
                messages.success(request, f'User {user.get_full_name()} {action} successfully!')
                
                UserActivityLog.objects.create(
                    user=request.user,
                    action=f'USER_{action.upper()}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    data={'target_user': user.email}
                )
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    
    return redirect('accounts:user_management')
