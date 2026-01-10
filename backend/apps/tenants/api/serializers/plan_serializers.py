from rest_framework import serializers

from apps.tenants.models import Plan


class PlanSerializer(serializers.ModelSerializer):
    """Serializer para listagem de planos."""

    class Meta:
        model = Plan
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'max_supporters',
            'max_messages_month',
            'max_campaigns',
            'max_whatsapp_sessions',
            'price',
            'features',
        ]
