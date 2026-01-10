"""
Serializers for WhatsAppSession model.
"""
import uuid
from rest_framework import serializers

from apps.whatsapp.models import WhatsAppSession


class WhatsAppSessionSerializer(serializers.ModelSerializer):
    """Full serializer for WhatsApp session detail view."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    remaining_messages = serializers.IntegerField(source='remaining_messages_today', read_only=True)
    is_connected = serializers.BooleanField(read_only=True)
    can_send_messages = serializers.BooleanField(read_only=True)

    class Meta:
        model = WhatsAppSession
        fields = [
            'id', 'name', 'instance_name', 'status', 'status_display',
            'phone_number', 'daily_message_limit', 'messages_sent_today',
            'remaining_messages', 'is_connected', 'can_send_messages',
            'is_healthy', 'is_active', 'last_health_check',
            'access_token', 'webhook_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'instance_name', 'status', 'phone_number',
            'messages_sent_today', 'is_healthy', 'last_health_check',
            'webhook_url',
            'created_at', 'updated_at'
        ]


class WhatsAppSessionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for session list view."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    remaining_messages = serializers.IntegerField(source='remaining_messages_today', read_only=True)

    class Meta:
        model = WhatsAppSession
        fields = [
            'id', 'name', 'status', 'status_display', 'phone_number',
            'messages_sent_today', 'daily_message_limit', 'remaining_messages',
            'is_active', 'is_healthy'
        ]


class WhatsAppSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating WhatsApp sessions."""

    class Meta:
        model = WhatsAppSession
        fields = ['name', 'daily_message_limit']

    def validate_name(self, value):
        """Validate session name is unique."""
        qs = WhatsAppSession.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Já existe uma sessão com este nome.")
        return value

    def validate_daily_message_limit(self, value):
        """Validate daily limit is reasonable."""
        if value < 10:
            raise serializers.ValidationError("Limite mínimo é 10 mensagens por dia.")
        if value > 10000:
            raise serializers.ValidationError("Limite máximo é 10.000 mensagens por dia.")
        return value

    def create(self, validated_data):
        """Create session with unique instance name."""
        # Generate unique instance name for Evolution API
        validated_data['instance_name'] = f"voxpop_{uuid.uuid4().hex[:8]}"
        return super().create(validated_data)


class QRCodeSerializer(serializers.Serializer):
    """Serializer for QR code response."""
    qr_code = serializers.CharField(help_text="Base64 encoded QR code image")
    generated_at = serializers.DateTimeField()
    expires_in_seconds = serializers.IntegerField()
    status = serializers.CharField()
