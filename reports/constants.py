WIDGET_CONFIG_SCHEMA = {
    'bar_chart': {
        'label': {'type': 'string', 'default': 'Value'},
        'colors': {'type': 'array', 'default': ['#36a2eb', '#ff6384', '#ffcd56']},
        'stacked': {'type': 'boolean', 'default': False}
    },
    'line_chart': {
        'label': {'type': 'string', 'default': 'Value'},
        'fill': {'type': 'boolean', 'default': False},
        'tension': {'type': 'number', 'default': 0.4}
    },
    'pie_chart': {
        'colors': {'type': 'array', 'default': ['#36a2eb', '#ff6384', '#ffcd56', '#4bc0c0']},
        'cutout': {'type': 'string', 'default': '0%'}
    },
    'table': {
        'columns': {'type': 'array', 'default': []},
        'page_size': {'type': 'number', 'default': 10}
    },
    'metric': {
        'prefix': {'type': 'string', 'default': ''},
        'suffix': {'type': 'string', 'default': ''},
        'color': {'type': 'string', 'default': '#36a2eb'}
    },
    'progress': {
        'color': {'type': 'string', 'default': '#36a2eb'},
        'show_percentage': {'type': 'boolean', 'default': True}
    }
}

DATA_SOURCE_CONFIG = {
    'projects.status': {
        'description': 'Distribution of projects by status',
        'compatible_widgets': ['pie_chart', 'bar_chart', 'table']
    },
    'tasks.completion': {
        'description': 'Task completion by project',
        'compatible_widgets': ['bar_chart', 'line_chart', 'table']
    },
    'time.tracking': {
        'description': 'Time spent by project',
        'compatible_widgets': ['bar_chart', 'line_chart', 'table'],
        'config': {
            'days': {'type': 'number', 'default': 30}
        }
    },
    'invoices.status': {
        'description': 'Invoice amounts by status',
        'compatible_widgets': ['pie_chart', 'bar_chart', 'table']
    },
    'team.performance': {
        'description': 'Team member productivity',
        'compatible_widgets': ['bar_chart', 'table']
    },
    'clients.billing': {
        'description': 'Client billing summary',
        'compatible_widgets': ['bar_chart', 'table']
    }
}