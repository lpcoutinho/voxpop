from rest_framework import serializers
from django.utils import timezone

from apps.campaigns.models import Campaign, CampaignItem
from apps.whatsapp.api.serializers.session_serializers import WhatsAppSessionSerializer
from apps.supporters.models import Tag, Segment

class CampaignItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignItem
        fields = [
            'id', 'recipient_name', 'recipient_phone', 
            'status', 'sent_at', 'delivered_at', 'read_at', 
            'error_message'
        ]

class CampaignListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    whatsapp_session_name = serializers.CharField(source='whatsapp_session.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'description', 'status', 'status_display',
            'scheduled_at', 'total_recipients', 'messages_sent', 
            'messages_delivered', 'messages_read', 'messages_failed',
            'whatsapp_session_name', 'created_by_name', 'created_at'
        ]

class CampaignDetailSerializer(CampaignListSerializer):
    items = CampaignItemSerializer(many=True, read_only=True)
    target_tags_display = serializers.StringRelatedField(source='target_tags', many=True)
    target_segment_name = serializers.CharField(source='target_segment.name', read_only=True)

    # Métricas computadas a partir dos itens reais (fonte de verdade)
    total_recipients = serializers.SerializerMethodField()
    messages_sent = serializers.SerializerMethodField()
    messages_delivered = serializers.SerializerMethodField()
    messages_read = serializers.SerializerMethodField()
    messages_failed = serializers.SerializerMethodField()

    class Meta(CampaignListSerializer.Meta):
        fields = CampaignListSerializer.Meta.fields + [
            'message', 'media_url', 'media_type',
            'target_segment', 'target_segment_name',
            'target_tags', 'target_tags_display', 'target_groups',
            'items', 'whatsapp_session'
        ]

    def _get_items(self, obj):
        """Cache dos itens para evitar múltiplas queries."""
        if not hasattr(obj, '_cached_items_list'):
            obj._cached_items_list = list(obj.items.all())
        return obj._cached_items_list

    def get_total_recipients(self, obj):
        return len(self._get_items(obj))

    def get_messages_sent(self, obj):
        return sum(1 for i in self._get_items(obj) if i.status in ('sent', 'delivered', 'read'))

    def get_messages_delivered(self, obj):
        return sum(1 for i in self._get_items(obj) if i.status in ('delivered', 'read'))

    def get_messages_read(self, obj):
        return sum(1 for i in self._get_items(obj) if i.status == 'read')

    def get_messages_failed(self, obj):
        return sum(1 for i in self._get_items(obj) if i.status == 'failed')

class CampaignCreateSerializer(serializers.ModelSerializer):
    target_groups = serializers.ListField(
        child=serializers.ChoiceField(choices=['leads', 'supporters', 'team']),
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Campaign
        fields = [
            'name', 'description', 'message', 
            'media_url', 'media_type',
            'whatsapp_session', 'scheduled_at',
            'target_segment', 'target_tags', 'target_groups'
        ]

    def validate_scheduled_at(self, value):
        if value and value < timezone.now():
            raise serializers.ValidationError("A data agendada deve ser futura.")
        return value

    def validate(self, data):
        """Garante que pelo menos um público alvo foi selecionado."""
        target_tags = data.get('target_tags', [])
        target_groups = data.get('target_groups', [])
        
        # target_tags é ManyToMany, no create ele vem como lista de IDs se usar PrimaryKeyRelatedField padrão,
        # mas aqui o ModelSerializer lida com isso no save(). 
        # No validate(), se o campo for M2M, ele pode não estar populado ainda ou vir como lista.
        # Vamos checar se a lista não está vazia.
        
        if not target_tags and not target_groups:
            raise serializers.ValidationError("Selecione pelo menos um público alvo (Tags ou Grupos).")
            
        return data