"""
Serializers for Dashboard metrics.
"""
from rest_framework import serializers

from apps.dashboard.models import DailyMetrics


class OverviewSerializer(serializers.Serializer):
    """Serializer for dashboard overview cards."""
    total_supporters = serializers.IntegerField()
    new_supporters_today = serializers.IntegerField()
    messages_sent_month = serializers.IntegerField()
    messages_sent_today = serializers.IntegerField()
    delivery_rate = serializers.FloatField()
    read_rate = serializers.FloatField()
    active_campaigns = serializers.IntegerField()
    whatsapp_sessions = serializers.DictField()


class DailyMetricsSerializer(serializers.ModelSerializer):
    """Serializer for daily metrics."""

    class Meta:
        model = DailyMetrics
        fields = [
            'date', 'new_supporters', 'total_supporters',
            'messages_sent', 'messages_delivered', 'messages_read', 'messages_failed',
            'delivery_rate', 'read_rate',
            'campaigns_created', 'campaigns_completed'
        ]


class MetricsQuerySerializer(serializers.Serializer):
    """Serializer for validating metrics query params."""
    start = serializers.DateField(required=True)
    end = serializers.DateField(required=True)

    def validate(self, attrs):
        """Validate date range."""
        if attrs['start'] > attrs['end']:
            raise serializers.ValidationError({
                'start': 'Data inicial deve ser anterior à data final.'
            })

        # Limit range to 90 days
        from datetime import timedelta
        if (attrs['end'] - attrs['start']).days > 90:
            raise serializers.ValidationError({
                'end': 'O período máximo é de 90 dias.'
            })

        return attrs
