from rest_framework import serializers
from projects.models import Project
from .models import Task, TimeEntry, RecurringTask
from projects.serializers import ProjectSerializer
from team.models import TeamMember
from team.serializers import UserSerializer

class TaskSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    project = ProjectSerializer(read_only=True)
    assignees = UserSerializer(many=True, read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        source='project',
        write_only=True
    )
    assignee_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=TeamMember.objects.all(),
        source='assignees',
        write_only=True
    )
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'status_display',
            'priority', 'priority_display', 'due_date', 'project',
            'project_id', 'assignees', 'assignee_ids', 'created_at',
            'updated_at', 'estimated_duration'
        ]

class TimeEntrySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    task = TaskSerializer(read_only=True)
    duration = serializers.DurationField(read_only=True)
    
    class Meta:
        model = TimeEntry
        fields = [
            'id', 'user', 'task', 'start_time', 'end_time', 'duration',
            'description', 'is_billed', 'invoice', 'created_at'
        ]
    
    def validate(self, data):
        if data.get('end_time') and data['end_time'] < data['start_time']:
            raise serializers.ValidationError("End time must be after start time")
        return data

class RecurringTaskSerializer(serializers.ModelSerializer):
    base_task = TaskSerializer(read_only=True)
    
    class Meta:
        model = RecurringTask
        fields = [
            'id', 'base_task', 'recurrence', 'next_run', 'last_run',
            'total_runs', 'is_active', 'created_at'
        ]