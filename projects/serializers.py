from rest_framework import serializers
from chat.consumers import User
from .models import Project
from clients.models import Client

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'company', 'user']

class ProjectSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress = serializers.SerializerMethodField()
    client = ClientSerializer(read_only=True)
    team_members = UserSerializer(many=True, read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(),
        source='client',
        write_only=True
    )
    team_member_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        source='team_members',
        write_only=True
    )
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'status', 'status_display',
            'start_date', 'deadline', 'budget', 'progress',
            'client', 'client_id', 'team_members', 'team_member_ids',
            'created_at', 'updated_at'
        ]
    
    def get_progress(self, obj):
        return obj.progress_percentage

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['title', 'description', 'status', 'start_date', 'deadline', 'budget', 'client', 'team_members']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)