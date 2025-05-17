from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from clients.models import Client
from team.models import TeamMember

class Project(models.Model):
    STATUS_CHOICES = (
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    title = models.CharField(max_length=200)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    start_date = models.DateField()
    deadline = models.DateField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    team_members = models.ManyToManyField(TeamMember, related_name='projects')
    created_by = models.ForeignKey(TeamMember, on_delete=models.CASCADE, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    progress_percentage = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title

    def calculate_progress_percentage(self):
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = self.tasks.filter(status='completed').count()
        return round((completed_tasks / total_tasks) * 100)

    # Remove this save override to prevent premature query of self.tasks
    # def save(self, *args, **kwargs):
    #     self.progress_percentage = self.calculate_progress_percentage()
    #     super().save(*args, **kwargs)

# ✅ Post-save signal to calculate progress after saving
@receiver(post_save, sender=Project)
def update_progress_percentage(sender, instance, created, **kwargs):
    if not created:  # Only update on edits
        progress = instance.calculate_progress_percentage()
        if progress != instance.progress_percentage:
            Project.objects.filter(pk=instance.pk).update(progress_percentage=progress)
