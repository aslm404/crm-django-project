from .models import TeamMember

def user_permissions(request):
    """
    Adds user permissions to template context
    """
    if not request.user.is_authenticated:
        return {'user_perms': set(), 'is_admin': False, 'is_client': False}
    return {
        'user_perms': request.user.get_all_permissions(),
        'is_admin': request.user.role == 'admin',
        'is_client': request.user.role == 'client',
    }

def active_timer(request):
    """
    Adds active timer information to template context
    """
    if not request.user.is_authenticated:
        return {}
    try:
        from tasks.models import TimeEntry
        active_timer = TimeEntry.objects.filter(
            user=request.user,
            end_time__isnull=True
        ).first()
        return {
            'active_timer': active_timer,
            'active_task': active_timer.task if active_timer else None
        }
    except ImportError:
        return {}

def team_context(request):
    """
    General team-related context for all templates
    """
    if not request.user.is_authenticated:
        return {}
    return {
        'user_roles': dict(TeamMember.ROLE_CHOICES),
        'current_user': request.user,
    }

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

def navbar_menu(request):
    url_name = request.resolver_match.url_name if request.resolver_match else ''
    return {
        'menu_items': [
            {'label': 'Dashboard', 'url_name': 'team:dashboard', 'icon': 'bi-speedometer2', 'active': url_name == 'team:dashboard'},
            {'label': 'Chat', 'url_name': 'chat:conversation_list', 'icon': 'bi-chat-dots', 'active': 'chat' in url_name},
            {'label': 'Team', 'url_name': 'team:team_list', 'icon': 'bi-people', 'active': 'team' in url_name and 'dashboard' not in url_name},
            {'label': 'Clients', 'url_name': 'clients:list', 'icon': 'bi-person-lines-fill', 'active': 'clients' in url_name},
            {'label': 'Support', 'url_name': 'support:ticket_list', 'icon': 'bi-life-preserver', 'active': 'support' in url_name},
            {'label': 'Projects', 'url_name': 'projects:list', 'icon': 'bi-kanban', 'active': 'projects' in url_name},
            {'label': 'Tasks', 'url_name': 'tasks:list', 'icon': 'bi-check-square', 'active': 'tasks' in url_name},
            {'label': 'Invoices', 'url_name': 'invoices:list', 'icon': 'bi-receipt', 'active': 'invoices' in url_name},
            {'label': 'Reports', 'url_name': 'reports:dashboard_list', 'icon': 'bi-bar-chart-line', 'active': 'reports' in url_name},
        ]
    }
