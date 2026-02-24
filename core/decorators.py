from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(allowed_roles=None, redirect_url='accounts:login'):
    """
    Decorator to check if user has required role
    Usage: @role_required(['CHIEF_OFFICER', 'COUNTY_SECRETARY'])
    """
    if allowed_roles is None:
        allowed_roles = []
    
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(redirect_url)
            
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('core:dashboard')
        return _wrapped_view
    return decorator

def group_required(group_names):
    """
    Decorator to check if user belongs to required groups
    Usage: @group_required(['Chief Officers', 'CPSB Board'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            if request.user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('core:dashboard')
        return _wrapped_view
    return decorator