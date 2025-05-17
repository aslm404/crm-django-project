from django.db import models
from django.db.models import JSONField
from team.models import TeamMember

class Dashboard(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(TeamMember, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_shared = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class Widget(models.Model):
    WIDGET_TYPES = (
        ('bar_chart', 'Bar Chart'),
        ('line_chart', 'Line Chart'),
        ('pie_chart', 'Pie Chart'),
        ('table', 'Data Table'),
        ('metric', 'Single Metric'),
        ('progress', 'Progress Bar'),
    )
    
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets')
    title = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    data_source = models.CharField(max_length=100)  # e.g., 'projects.status'
    width = models.PositiveIntegerField(default=4)  # Bootstrap columns (1-12)
    height = models.PositiveIntegerField(default=300)  # pixels
    position = models.PositiveIntegerField()
    config = JSONField(default=dict)  # Custom widget configuration
    refresh_interval = models.PositiveIntegerField(default=0)  # minutes (0=manual)
    
    class Meta:
        ordering = ['position']
    
    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"