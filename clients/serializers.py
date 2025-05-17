from rest_framework import serializers
from .models import Client, ClientNote, ClientFile
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class ClientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'user', 'company', 'address', 'website', 'vat_number',
            'payment_terms', 'preferred_currency', 'logo', 'created_at', 'phone', 'updated_at'
        ]

class ClientNoteSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ClientNote
        fields = ['id', 'client', 'content', 'created_by', 'is_public', 'created_at']
        read_only_fields = ['created_by', 'created_at']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class ClientFileSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ClientFile
        fields = ['id', 'client', 'file', 'file_url', 'description', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['uploaded_by', 'uploaded_at']
    
    def get_file_url(self, obj):
        return obj.file.url if obj.file else None
    
    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)