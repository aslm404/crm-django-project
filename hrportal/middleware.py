from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ActivityTrackingMiddleware:
    """
    Tracks user activity and updates last_activity field
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated:
            user = request.user
            user.last_activity = timezone.now()
            user.save(update_fields=['last_activity'])
        
        return response

class RoleBasedAccessMiddleware:
    """
    Checks user role and permissions before allowing access
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        exempt_paths = [
            reverse('login'),
            reverse('logout'),
            '/admin/',
            '/static/',
            '/media/',
        ]
        
        if any(request.path.startswith(path) for path in exempt_paths):
            return self.get_response(request)
        
        if request.user.is_authenticated:
            if not request.user.is_active:
                logger.warning(f"Inactive user {request.user} tried to access {request.path}")
                return HttpResponseRedirect(reverse('login') + '?inactive=1')
            
            if request.path.startswith('/admin/') and not request.user.is_staff:
                logger.warning(f"Non-staff user {request.user} tried to access admin panel")
                return HttpResponseForbidden("Access denied")
        
        return self.get_response(request)

class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Content Security Policy update
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
        )
        
        # Additional headers (optional)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response


class RequestLoggingMiddleware:
    """
    Logs all incoming requests for debugging and auditing
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info(
            f"Request: {request.method} {request.path} "
            f"User: {request.user if request.user.is_authenticated else 'Anonymous'} "
            f"IP: {request.META.get('REMOTE_ADDR')}"
        )
        
        response = self.get_response(request)
        
        logger.info(f"Response: {request.method} {request.path} -> {response.status_code}")
        
        return response

class MaintenanceModeMiddleware:
    """
    Enables maintenance mode with configurable settings
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, 'MAINTENANCE_MODE', False):
            exempt_paths = [
                reverse('login'),
                '/admin/',
                '/static/',
                '/media/',
            ]
            
            if not any(request.path.startswith(path) for path in exempt_paths):
                return HttpResponseRedirect(reverse('maintenance'))
        
        return self.get_response(request)