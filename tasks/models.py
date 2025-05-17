from django.db import models
from projects.models import Project
from team.models import TeamMember
from invoices.models import Invoice

class Task(models.Model):
    STATUS_CHOICES = (
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField()
    assignees = models.ManyToManyField(TeamMember, related_name='assigned_tasks')
    created_by = models.ForeignKey(TeamMember, on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_duration = models.DurationField(null=True, blank=True)
    complexity = models.FloatField(default=1.0, help_text="Task complexity (1-5)")
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

class TimeEntry(models.Model):
    user = models.ForeignKey(TeamMember, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_entries')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_billed = models.BooleanField(default=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='time_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if self.end_time and self.start_time:
            self.duration = self.end_time - self.start_time
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user} - {self.task} ({self.duration})"

class RecurrencePattern(models.Model):
    INTERVAL_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    )
    
    WEEKDAY_CHOICES = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    interval = models.CharField(max_length=20, choices=INTERVAL_CHOICES)
    frequency = models.PositiveIntegerField(default=1)
    weekdays = models.JSONField(blank=True, null=True)
    month_day = models.PositiveIntegerField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    max_occurrences = models.PositiveIntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_interval_display()} (Every {self.frequency})"

class RecurringTask(models.Model):
    base_task = models.ForeignKey(Task, on_delete=models.CASCADE)
    recurrence = models.ForeignKey(RecurrencePattern, on_delete=models.CASCADE)
    next_run = models.DateField()
    last_run = models.DateField(null=True, blank=True)
    total_runs = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Recurring: {self.base_task.title}"