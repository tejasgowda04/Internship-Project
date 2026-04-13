from .models import ImpactMetrics


def global_context(request):
    """Inject global template variables."""
    context = {
        'platform_name': 'FoodWasteChain',
    }

    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        context['user_role'] = request.user.profile.role
        context['user_org'] = request.user.profile.organization_name

    try:
        metrics = ImpactMetrics.get_metrics()
        context['global_metrics'] = metrics
    except Exception:
        pass

    return context
