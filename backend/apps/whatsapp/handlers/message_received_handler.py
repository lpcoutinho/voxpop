"""
Handler para evento messages.upsert (nova mensagem recebida).
"""
import logging
from typing import Dict, Any, Optional
from django.http import HttpResponse

from apps.messaging.models import Message
from apps.supporters.models import Supporter
from apps.whatsapp.models import WhatsAppSession
from apps.whatsapp.handlers.base_handler import BaseWebhookHandler
from apps.whatsapp.controllers.webhook_controller import (
    create_success_response,
    create_error_response
)

logger = logging.getLogger(__name__)


class MessageReceivedHandler(BaseWebhookHandler):
    """
    Handler para evento messages.upsert.
    Processa novas mensagens recebidas dos destinatários.
    """

    def handle(self, request) -> HttpResponse:
        """
        Processa nova mensagem recebida do WhatsApp.
        """
        self.event_data = self.get_event_data(request)
        if not self.event_data:
            return self.create_error_response(
                error_code='INVALID_EVENT',
                error_message='Dados do evento não encontrados'
            )

        direction = 'in'  # Mensagem recebida

        # Extrai dados da mensagem
        data = self.event_data.get('data', {})
        message_content = self.get_message_content()
        remote_jid = data.get('remoteJid', '')
        phone_number = self.get_phone_number()

        if not message_content:
            logger.error("Conteúdo da mensagem não encontrado")
            return self.create_error_response(
                error_code='INVALID_MESSAGE',
                error_message='Conteúdo da mensagem não fornecido'
            )

        # Valida se o número de telefone está cadastrado
        if not phone_number.startswith('+'):
            logger.error(f"Número de telefone inválido: {phone_number}")
            return self.create_error_response(
                error_code='INVALID_PHONE',
                error_message='Número de telefone deve começar com + (DD)'
            )

        # Busca o apoiador pelo telefone
        try:
            # Normaliza o telefone para busca
            phone_clean = phone_number.replace('+', '').replace(' ', '')
            if not phone_clean:
                return self.create_error_response(
                    error_code='INVALID_PHONE',
                    error_message='Número de telefone vazio após limpeza'
                )

            # Verifica se está cadastrado
            from apps.supporters.models import Supporter

            # Primeiro tenta pelo telefone completo
            supporter = Supporter.objects.filter(phone__number=phone_clean).first()

            # Se não encontrar, pode ser um número novo, tentar sem o DDD
            if not supporter:
                # Tenta sem DDD
                ddd_phone = phone_clean[-2:] if len(phone_clean) >= 10 else phone_clean[-11:]
                supporter = Supporter.objects.filter(phone__endswith=ddd_phone).first()

            # Se ainda não encontrou, marca como desconhecido
            if not supporter:
                logger.warning(f"Destinatário desconhecido: {phone_number}")
                # Cria novo apoiador temporário (pode ser confirmado depois)
                supporter = Supporter.objects.create(
                    name=f"Desconhecido {phone_number}",
                    phone=phone_clean,
                    is_temporary=True  # Marcado como temporário
                )

            logger.info(f"Apoiador encontrado (ou criado): {supporter.name}")

        # Verifica se o apoiador está ativo
        if not supporter.is_active:
            logger.warning(f"Apoiador inativo: {supporter.name}")
            return self.create_error_response(
                error_code='SUPPORTER_INACTIVE',
                error_message='Apoiador não está ativo'
            )

        # Valida se é apoiador (não blacklist)
        if supporter.status == 'blacklist':
            logger.warning(f"Apoiador em blacklist: {supporter.name}")
            return self.create_error_response(
                error_code='SUPPORTER_BLACKLISTED',
                error_message='Apoiador está na blacklist'
            )

        # Valida se é apoiador (ou lead)
        if supporter.status not in ['apoiador', 'lead']:
            logger.warning(f"Apoiador não é lead/apoiador: {supporter.name}")
            return self.create_error_response(
                error_code='INVALID_SUPPORTER_STATUS',
                error_message='Destinatário não é um apoiador ativo'
            )

        # Cria a mensagem no banco
        message = Message.objects.create(
            supporter=supporter,
            campaign_item=None,  # Mensagem recebida não está vinculada a campanha ainda
            direction=direction,
            status='received',
            message_type='text',
            content=message_content,
            external_id=remote_jid,
            created_at=self.get_timestamp(),
        )

        logger.info(f"Nova mensagem recebida de {phone_number}: {message_content[:50]}...")

        return create_success_response(
            data={
                'direction': direction,
                'status': 'received',
                'phone_number': phone_number,
                'message_type': 'text',
                'content': message_content[:100] if len(message_content) > 100 else message_content,
                'external_id': remote_jid,
                'timestamp': self.get_timestamp(),
            },
            message="Mensagem processada com sucesso"
        )

    def _process_message_upsert(
        self,
        session: WhatsAppSession,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Processa evento messages.upsert (chamado pela task).

        Args:
            session: Sessão WhatsApp que recebeu o evento
            payload: Payload completo do webhook

        Returns:
            Dict com resultado do processamento
        """
        try:
            # Extrai dados do payload
            data = payload.get('data', {})
            message_content = data.get('text', '')
            remote_jid = data.get('remoteJid', '')
            phone_number = remote_jid.split('@')[0] if remote_jid else ''
            message_type = data.get('messageType', 'text')

            if not message_content and message_type == 'text':
                logger.warning("Mensagem sem conteúdo")
                return {'error': 'Mensagem sem conteúdo'}

            # Normaliza telefone
            phone_clean = phone_number.replace('+', '').replace(' ', '')

            # Busca apoiador
            supporter = Supporter.objects.filter(phone__endswith=phone_clean[-9:]).first()

            if not supporter:
                logger.warning(f"Supporter não encontrado para {phone_number}")
                return {'error': 'Supporter não encontrado', 'phone': phone_number}

            # Cria mensagem no banco
            message = Message.objects.create(
                supporter=supporter,
                campaign_item=None,
                direction='in',
                status='received',
                message_type=message_type,
                content=message_content,
                external_id=remote_jid,
            )

            logger.info(f"Mensagem recebida processada: {message.id}")

            return {
                'success': True,
                'message_id': message.id,
                'supporter': supporter.name,
                'content': message_content[:50]
            }

        except Exception as e:
            logger.exception(f"Erro ao processar message upsert: {e}")
            return {'error': str(e)}
