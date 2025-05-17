from .models import Widget

def create_default_widgets(dashboard):
    """
    Create default widgets for a new dashboard
    """
    default_widgets = [
        {
            'title': 'Project Status',
            'widget_type': 'pie_chart',
            'data_source': 'projects.status',
            'width': 4,
            'height': 300,
            'position': 1,
            'config': {'colors': ['#36a2eb', '#ff6384', '#ffcd56']},
        },
        {
            'title': 'Task Completion',
            'widget_type': 'bar_chart',
            'data_source': 'tasks.completion',
            'width': 4,
            'height': 300,
            'position': 2,
            'config': {'stacked': False},
        },
    ]
    
    for index, widget_data in enumerate(default_widgets, start=1):
        Widget.objects.create(dashboard=dashboard, **widget_data)