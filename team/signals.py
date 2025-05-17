from django.db.models.signals import post_save, pre_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.core.cache import cache
from .models import TeamMember, Role
import logging
import re

logger = logging.getLogger(__name__)

@receiver(post_save, sender=TeamMember)
def assign_default_permissions(sender, instance, created, **kwargs):
    """
    Assign default permissions based on user role when created
    """
    if created and instance.role == 'client':
        clients_group, _ = Group.objects.get_or_create(name='Clients')
        instance.groups.add(clients_group)
        logger.info(f"Assigned client permissions to {instance.email}")
    cache.delete(f'user_{instance.id}_permissions')

@receiver(m2m_changed, sender=TeamMember.groups.through)
def clear_permission_cache_on_group_change(sender, instance, action, **kwargs):
    """
    Clear permission cache when user groups change
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        cache.delete(f'user_{instance.id}_permissions')
        logger.info(f"Cleared permission cache for {instance.email} due to group change")

@receiver(m2m_changed, sender=Role.permissions.through)
def clear_user_cache_on_role_change(sender, instance, action, pk_set, **kwargs):
    """
    Clear permission cache for all users with this role when role permissions change
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        for user in instance.teammember_set.all():
            cache.delete(f'user_{user.id}_permissions')
        logger.info(f"Cleared permission cache for all users with role {instance.name}")

@receiver(pre_save, sender=TeamMember)
def set_username_from_email(sender, instance, **kwargs):
    """
    Automatically set username from email if not provided, ensuring uniqueness
    """
    if not instance.username and instance.email:
        # Sanitize email to create a valid username
        username = re.sub(r'[^\w.@+-]', '', instance.email.split('@')[0]).lower()
        base_username = username
        counter = 1
        while TeamMember.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        instance.username = username
        logger.debug(f"Set username to {instance.username} for {instance.email}")