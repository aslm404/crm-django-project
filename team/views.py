from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.http import Http404
from django.shortcuts import redirect, render
from .models import TeamMember, Role
from .forms import LoginForm, TeamMemberCreationForm, TeamMemberUpdateForm, RoleForm, ClientRegistrationForm
from rest_framework import viewsets
from .serializers import UserSerializer, RoleSerializer
from rest_framework.permissions import IsAdminUser
import logging
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)

class CustomLoginView(LoginView):
    """
    Custom login view that handles 'remember me' session logic
    """
    form_class = LoginForm
    template_name = 'team/auth/login.html'

    def form_valid(self, form):
        remember_me = self.request.POST.get('remember_me')
        if not remember_me:
            self.request.session.set_expiry(0)
        user = form.get_user()
        logger.info(f"User {user.username} logged in successfully.")
        return super().form_valid(form)

class ClientRegistrationView(CreateView):
    model = TeamMember
    form_class = ClientRegistrationForm
    template_name = 'team/auth/register.html'
    success_url = reverse_lazy('team:profile')

    def form_valid(self, form):
        form.instance.is_active = True
        if self.request.user.is_authenticated and self.request.user.role == 'admin':
            form.instance.created_by = self.request.user
        response = super().form_valid(form)
        username = form.instance.email
        password = form.cleaned_data.get('password1')
        role = form.cleaned_data.get('role')
        user = authenticate(self.request, username=username, password=password)
        if user:
            login(self.request, user)
            logger.info(f"User {user.username} registered as {role} and logged in.")
        else:
            logger.warning(f"Authentication failed for newly registered user {username} as {role}.")
        return response

@method_decorator(login_required, name='dispatch')
class TeamListView(ListView):
    model = TeamMember
    template_name = 'team/list.html'
    context_object_name = 'team_members'

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return TeamMember.objects.none()
        if user.is_superuser:
            return TeamMember.objects.filter(is_active=True).exclude(role='client').select_related('custom_role')
        elif user.role == 'admin':
            return TeamMember.objects.filter(
                is_active=True, created_by=user, role='staff'
            ).select_related('custom_role')
        elif user.role == 'staff' and user.created_by:
            return TeamMember.objects.filter(
                is_active=True, created_by=user.created_by, role='staff'
            ).select_related('custom_role')
        return TeamMember.objects.filter(pk=user.pk).select_related('custom_role')

@method_decorator(login_required, name='dispatch')
class TeamDetailView(DetailView):
    model = TeamMember
    template_name = 'team/detail.html'
    context_object_name = 'member'

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            # Superuser can view all active team members
            return TeamMember.objects.filter(is_active=True).select_related('custom_role')

        elif user.role == 'admin':
            # Admin can view their staff
            return TeamMember.objects.filter(
                is_active=True,
                created_by=user,
                role='staff'
            ).select_related('custom_role')

        elif user.role == 'staff' and user.created_by:
            # Staff can view other staff under same admin, and also the admin's profile
            return TeamMember.objects.filter(
                is_active=True,
                created_by=user.created_by,
                role='staff'
            ).select_related('custom_role') | TeamMember.objects.filter(
                pk=user.created_by.pk,
                is_active=True
            ).select_related('custom_role')

        # Default fallback: only view own profile
        return TeamMember.objects.filter(pk=user.pk).select_related('custom_role')

@method_decorator(login_required, name='dispatch')
class TeamUpdateView(UpdateView):
    model = TeamMember
    form_class = TeamMemberUpdateForm
    template_name = 'team/form.html'
    success_url = reverse_lazy('team:team_list')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        if user.is_superuser or (user.role == 'admin' and (obj.created_by == user or obj == user)) or (user.role == 'staff' and obj == user):
            return obj
        raise Http404("You do not have permission to edit this profile.")

@method_decorator(login_required, name='dispatch')
class TeamCreateView(CreateView):
    model = TeamMember
    form_class = TeamMemberCreationForm
    template_name = 'team/form.html'
    success_url = reverse_lazy('team:team_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.role == 'admin':
            raise Http404("Only admins can add team members.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.is_active = True
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        logger.info(f"Team member {form.instance.username} created by {self.request.user.username}")
        return response

@method_decorator(login_required, name='dispatch')
class RoleListView(ListView):
    model = Role
    template_name = 'team/roles/list.html'
    context_object_name = 'roles'

@method_decorator(login_required, name='dispatch')
class RoleCreateView(CreateView):
    model = Role
    form_class = RoleForm
    template_name = 'team/roles/form.html'
    success_url = reverse_lazy('team:role_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.role == 'admin':
            raise Http404("Only admins can create roles.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(f"Role {form.instance.name} created")
        return response

@method_decorator(login_required, name='dispatch')
class RoleUpdateView(UpdateView):
    model = Role
    form_class = RoleForm
    template_name = 'team/roles/form.html'
    success_url = reverse_lazy('team:role_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.role == 'admin':
            raise Http404("Only admins can update roles.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(f"Role {form.instance.name} updated")
        return response

@login_required
def profile_view(request):
    return render(request, 'team/profile.html', {'user': request.user})

@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = TeamMemberUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            logger.info(f"User {request.user.username} updated profile")
            return redirect('team:profile')
    else:
        form = TeamMemberUpdateForm(instance=request.user)
    return render(request, 'team/profile_edit.html', {'form': form})

class UserViewSet(viewsets.ModelViewSet):
    queryset = TeamMember.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    required_permissions = ['team.view_teammember']

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser]
    required_permissions = ['team.view_role']

@method_decorator(login_required, name='dispatch')
class DashboardView(ListView):
    model = TeamMember
    template_name = 'team/dashboard.html'
    context_object_name = 'team_members'

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return TeamMember.objects.none()
        if user.is_superuser:
            return TeamMember.objects.filter(is_active=True).exclude(role='client').select_related('custom_role')
        elif user.role == 'admin':
            return TeamMember.objects.filter(
                is_active=True, created_by=user, role='staff'
            ).select_related('custom_role')
        elif user.role == 'staff' and user.created_by:
            return TeamMember.objects.filter(
                is_active=True, created_by=user.created_by, role='staff'
            ).select_related('custom_role')
        return TeamMember.objects.filter(pk=user.pk).select_related('custom_role')

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('team:dashboard')