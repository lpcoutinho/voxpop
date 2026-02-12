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
    start = serializers.DateField(required=False, allow_null=True)
    end = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        """Validate date range."""
        from datetime import timedelta, date

        # Se não foi fornecido, usar últimos 7 dias
        if 'start' not in attrs or attrs['start'] is None:
            attrs['start'] = date.today() - timedelta(days=7)

        if 'end' not in attrs or attrs['end'] is None:
            attrs['end'] = date.today()

        if attrs['start'] > attrs['end']:
            raise serializers.ValidationError({
                'start': 'Data inicial deve ser anterior à data final.'
            })

        # Limit range to 90 days
        if (attrs['end'] - attrs['start']).days > 90:
            raise serializers.ValidationError({
                'end': 'O período máximo é de 90 dias.'
            })

        return attrs
