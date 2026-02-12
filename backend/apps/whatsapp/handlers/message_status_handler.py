"""
Handler para evento messages.update (atualização de status de mensagem).
"""
import logging
from typing import Dict, Any
from django.utils import timezone
from django.http import HttpResponse
from apps.messaging.models import Message
from apps.whatsapp.handlers.base_handler import BaseWebhookHandler
from apps.whatsapp.controllers.webhook_controller import (
    create_success_response,
    create_error_response
)
from apps.whatsapp.models import WhatsAppSession

logger = logging.getLogger(__name__)


class MessageStatusHandler(BaseWebhookHandler):
    """
    Handler para evento messages.update.
    Atualiza o status de mensagens existentes com base no recebido.

    AGORA TAMBEM ATUALIZA:
    - CampaignItem.status baseado no status da mensagem
    - Contadores da campanha (messages_delivered, messages_read, messages_failed)
    - Timestamps (delivered_at, read_at)
    """

    def handle(self, request) -> HttpResponse:
        """
        Processa atualização de status de mensagem.
        """
        self.event_data = self.get_event_data(request)
        if not self.event_data:
            return self.create_error_response(
                error_code='INVALID_EVENT',
                error_message='Dados do evento não encontrados'
            )

        direction = self.event_data.get('data', {}).get('direction', '')
        if direction != 'out':
            logger.error(f"Direction inválida: {direction}")
            return self.create_error_response(
                error_code='INVALID_DIRECTION',
                error_message=f"Direction deve ser 'out', recebido: {direction}"
            )

        # Extrai dados
        message_id = self.event_data.get('data', {}).get('messageId')
        message_status = self.event_data.get('data', {}).get('status')

        if not message_id or not message_status:
            logger.error(f"messageId ou status não encontrados")
            return self.create_error_response(
                error_code='MISSING_FIELDS',
                error_message='IDs da mensagem ou status não fornecidos'
            )

        # Busca mensagens por message_id
        # Pode haver múltiplas mensagens com mesmo ID (para diferentes destinatários)
        messages = Message.objects.filter(whatsapp_message_id=message_id)

        if not messages.exists():
            logger.warning(f"Nenhuma mensagem encontrada com message_id: {message_id}")
            # Cria nova mensagem com status recebido
            Message.objects.create(
                direction='in',
                status=message_status,
                message_type='text',
                content=message_status,  # O status vem como texto no messages.update
                whatsapp_message_id=message_id,
                external_id=message_id,
            )
            logger.info(f"Status atualizado para nova mensagem (criada): {message_id} -> {message_status}")
            count = 1
        else:
            # Atualiza mensagens existentes
            count = messages.update(
                status=message_status.lower()
            )

            logger.info(f"Status atualizado para {count} mensagens existentes: {message_id} -> {message_status}")

        return create_success_response(
            data={
                'direction': direction,
                'messageId': message_id,
                'updatedCount': count
            },
            message=f"Status de {count} mensagens atualizado para '{message_status}'"
        )

    def _process_message_update(
        self,
        session: WhatsAppSession,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Processa evento messages.update (chamado pela task).

        Atualiza CampaignItem e contadores da campanha com base no status recebido.

        Args:
            session: Sessão WhatsApp que recebeu o evento
            payload: Payload completo do webhook

        Returns:
            Dict com resultado do processamento
        """
        from apps.campaigns.models import Campaign, CampaignItem

        try:
            # Extrai dados do payload
            data = payload.get('data', {})
            message_id = data.get('messageId')
            message_status = data.get('status', '').upper()
            key_id = data.get('keyId', '')

            logger.info("="*80)
            logger.info(f"📊 MESSAGES.UPDATE - Status: {message_status}")
            logger.info(f"   Message ID: {message_id}")
            logger.info(f"   Key ID: {key_id}")
            logger.info("="*80)

            # Valida dados
            if not message_id:
                return {'error': 'messageId não fornecido'}

            if not message_status:
                return {'error': 'status não fornecido'}

            # Busca CampaignItem correspondente
            campaign_item = CampaignItem.objects.filter(
                message_id=message_id
            ).first()

            if not campaign_item:
                logger.warning(f"CampaignItem não encontrada para message_id: {message_id}")
                logger.info(f"   ⚠️  CampaignItem não encontrada")
                return {
                    'success': True,
                    'message': 'CampaignItem não encontrado (não é mensagem de campanha)',
                    'message_id': message_id
                }

            campaign = campaign_item.campaign
            logger.info(f"   📢 Campanha: {campaign.name}")
            logger.info(f"   Destinatário: {campaign_item.recipient_name}")
            logger.info(f"   Status anterior: {campaign_item.status}")

            # Mapeia status da Evolution API para CampaignItem
            status_mapping = {
                'PENDING': CampaignItem.Status.PENDING,
                'SERVER_ACK': CampaignItem.Status.QUEUED,
                'DELIVERY_ACK': CampaignItem.Status.DELIVERED,
                'READ': CampaignItem.Status.READ,
                'FAILED': CampaignItem.Status.FAILED,
            }

            new_status = status_mapping.get(message_status)

            # Atualiza CampaignItem baseado no status
            update_fields = ['status', 'updated_at']
            update_message = ''

            if message_status == 'DELIVERY_ACK':
                # Mensagem entregue ao destinatário
                campaign_item.delivered_at = timezone.now()
                campaign_item.status = CampaignItem.Status.DELIVERED
                update_fields.extend(['delivered_at'])

                # Atualiza contador da campanha
                campaign.messages_delivered += 1
                campaign.save(update_fields=['messages_delivered'])

                update_message = f"✅ MENSAGEM ENTREGUE para {campaign_item.recipient_name}"

            elif message_status == 'READ':
                # Mensagem lida pelo destinatário
                campaign_item.read_at = timezone.now()
                campaign_item.status = CampaignItem.Status.READ
                update_fields.extend(['read_at'])

                # Atualiza contador da campanha
                campaign.messages_read += 1
                campaign.save(update_fields=['messages_read'])

                update_message = f"📖 MENSAGEM LIDA por {campaign_item.recipient_name}"

            elif message_status == 'FAILED':
                # Mensagem falhou
                campaign_item.status = CampaignItem.Status.FAILED
                campaign_item.error_message = f"Falha no envio: {message_status}"

                # Atualiza contador da campanha
                campaign.messages_failed += 1
                campaign.save(update_fields=['messages_failed'])

                update_message = f"❌ MENSAGEM FALHOU para {campaign_item.recipient_name}"

            elif message_status == 'SERVER_ACK':
                # Mensagem enviada para o servidor do WhatsApp
                if campaign_item.status == CampaignItem.Status.PENDING:
                    campaign_item.status = CampaignItem.Status.QUEUED
                    campaign_item.sent_at = timezone.now()
                    update_fields.extend(['sent_at'])

                    update_message = f"📤 MENSAGEM ENVIADA para {campaign_item.recipient_name}"

            # Salva CampaignItem
            campaign_item.save(update_fields=update_fields)

            logger.info(
                f"CampaignItem {campaign_item.id} atualizado: "
                f"{campaign_item.status} (msg: {message_status})"
            )

            logger.info(f"   Status atualizado: {campaign_item.status}")
            logger.info(f"   📊 Estatísticas da Campanha:")
            logger.info(f"      ✉️  Enviadas: {campaign.messages_sent}")
            logger.info(f"      ✅ Entregues: {campaign.messages_delivered}")
            logger.info(f"      📖 Lidas: {campaign.messages_read}")
            logger.info(f"      ❌ Falhas: {campaign.messages_failed}")

            return {
                'success': True,
                'campaign_id': campaign.id,
                'campaign_item_id': campaign_item.id,
                'status': campaign_item.status,
                'message_status': message_status
            }

        except CampaignItem.DoesNotExist:
            logger.warning(f"CampaignItem não encontrada para message_id: {message_id}")
            return {
                'success': True,
                'message': 'CampaignItem não encontrado',
                'message_id': message_id
            }
        except Exception as e:
            logger.exception(f"Erro ao processar message update: {e}")
            return {'error': str(e)}
