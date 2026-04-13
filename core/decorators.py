from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(role):
    """Generic role-checking decorator."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please log in to continue.')
                return redirect('login')
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'User profile not found.')
                return redirect('login')
            if request.user.profile.role != role:
                messages.error(request, f'Access denied. This page is for {role}s only.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def donor_required(view_func):
    """Restrict access to donors only."""
    return role_required('donor')(view_func)


def charity_required(view_func):
    """Restrict access to charities only."""
    return role_required('charity')(view_func)


def admin_required(view_func):
    """Restrict access to platform admins only."""
    return role_required('admin')(view_func)
