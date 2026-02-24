import json
from django.utils import timezone
from accounts.models import UserActivityLog

class AuditMiddleware:
    """Middleware to log user activities"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):

        response = self.get_response(request)
        
        if request.user.is_authenticated and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            pass
        
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Process view before execution"""
        request.start_time = timezone.now()
        return None