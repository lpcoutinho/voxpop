"""
Handler base para processamento de webhooks.
"""
import logging
from typing import Dict, Any, Optional
from django.http import HttpResponse
from apps.whatsapp.controllers.webhook_controller import (
    create_success_response,
    create_error_response
)

logger = logging.getLogger(__name__)


class BaseWebhookHandler:
    """
    Classe base para handlers de webhook.
    Fornece métodos comuns para processamento e resposta.
    """

    def __init__(self, request=None):
        """
        Inicializa o handler.
        """
        self.request = request
        self.event_data = None

    def get_event_data(self, key: str, default: Any = None) -> Any:
        """
        Obtém um dado do evento, com valor padrão opcional.
        """
        if not self.event_data:
            return None

        value = self.event_data.get(key, default)

        if value is None:
            return None

        return value

    def get_instance_name(self) -> Optional[str]:
        """
        Obtém o nome da instância do evento.
        """
        return self.event_data.get('instance', {}) if self.event_data else {}

    def get_timestamp(self) -> str:
        """
        Obtém o timestamp do evento.
        """
        return self.event_data.get('timestamp', '') if self.event_data else ''

    def get_phone_number(self) -> str:
        """
        Obtém o número de telefone do remetente.
        """
        # Extrai do payload principal (varia por tipo de evento)
        data = self.event_data.get('data', {})
        return data.get('remoteJid', '') if isinstance(data, dict) else ''

    def get_message_content(self) -> Optional[str]:
        """
        Obtém o conteúdo da mensagem.
        """
        data = self.event_data.get('data', {})

        # Para mensagens de texto, o conteúdo está em 'text'
        if isinstance(data, dict):
            if data.get('messageType') == 'text':
                return data.get('text', '')

        # Para mensagens com mídia, pode estar em 'caption' ou 'mediaUrl'
        if isinstance(data, dict):
            caption = data.get('caption', '')
            if caption:
                return caption
            media_url = data.get('mediaUrl', '')
            if media_url:
                return f"[Mídia: {media_url}]"

        return None

    def create_message(
        self,
        direction: str,
        status: str,
        message_content: str,
        phone_number: str,
        message_type: str = 'text',
        external_id: Optional[str] = None,
        whatsapp_id: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um registro de mensagem no banco de dados.
        """
        from apps.messaging.models import Message

        # Busca o destinatário (apoiador) pelo telefone
        from apps.supporters.models import Supporter

        try:
            # Normaliza o telefone (remove caracteres não numéricos)
            phone_clean = ''.join(c for c in phone_number if c.isdigit())

            # Busca o apoiador
            supporter = Supporter.objects.filter(phone=phone_clean).first()

            if not supporter:
                logger.warning(f"Destinatário não encontrado para {phone_number}")
                return {
                    'error': 'Destinatário não encontrado',
                    'phone_number': phone_number
                }

            # Cria a mensagem
            message = Message.objects.create(
                supporter=supporter,
                campaign_item=None,  # Mensagem recebida não está vinculada a campanha
                direction='in',  # Recebida
                status=status,
                message_type=message_type,
                content=message_content,
                external_id=external_id,
                whatsapp_id=whatsapp_id,
                created_at=timestamp,
            )

            logger.info(f"Mensagem recebida criada: {direction} {message_content[:50]}... para {phone_number}")

            return {
                'success': True,
                'message': 'Mensagem processada com sucesso',
                'message': message
            }

        except Exception as e:
            logger.exception(f"Erro ao criar mensagem: {e}")
            return {
                'error': f'Erro ao processar mensagem: {str(e)}',
                'phone_number': phone_number
            }

    def get_context_data(self) -> Dict[str, Any]:
        """
        Retorna dados de contexto para logs.
        """
        return {
            'handler': self.__class__.__name__,
            'event_type': self.get_event_data('event', ''),
            'instance': self.get_instance_name(),
            'timestamp': self.get_timestamp(),
            'phone_number': self.get_phone_number(),
        }

    def handle(self, request) -> HttpResponse:
        """
        Método principal que deve ser sobrescrito por subclasses.
        """
        raise NotImplementedError("Subclasses devem implementar o método handle()")
