from rest_framework import serializers


class TenantConfigSerializer(serializers.Serializer):
    signature = serializers.CharField(
        required=False, allow_blank=True, default='',
        help_text='Assinatura global do tenant. Suporta variáveis: {{name}}, {{city}}, etc.'
    )
    signature_enabled = serializers.BooleanField(
        required=False, default=False,
        help_text='Se ativado, a assinatura é anexada a todas as mensagens enviadas'
    )
