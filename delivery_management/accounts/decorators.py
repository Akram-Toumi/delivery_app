from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def admin_required(view_func):
    return role_required(['admin'])(view_func)

def manager_required(view_func):
    return role_required(['admin', 'manager'])(view_func)

def driver_required(view_func):
    return role_required(['admin', 'manager', 'driver'])(view_func)

def dispatcher_required(view_func):
    return role_required(['admin', 'manager', 'dispatcher'])(view_func)