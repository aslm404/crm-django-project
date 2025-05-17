from rest_framework import serializers
from .models import Dashboard, Widget
from team.serializers import UserSerializer

class WidgetSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_widget_type_display', read_only=True)
    
    class Meta:
        model = Widget
        fields = [
            'id', 'dashboard', 'title', 'widget_type', 'type_display',
            'data_source', 'width', 'height', 'position', 'config',
            'refresh_interval'
        ]

class DashboardSerializer(serializers.ModelSerializer):
    widgets = WidgetSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Dashboard
        fields = [
            'id', 'name', 'description', 'is_shared', 'widgets',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)