"""
WhatsApp Service for Evolution API integration.
"""
import logging
from typing import Any

import httpx
from django.conf import settings

from core.exceptions import EvolutionAPIError, WhatsAppConnectionError

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Serviço de integração com Evolution API.
    Gerencia sessões, QR codes e envio de mensagens.
    """

    def __init__(self):
        self.base_url = settings.EVOLUTION_API_URL.rstrip('/')
        self.api_key = settings.EVOLUTION_API_KEY
        self.timeout = 30.0

    def _get_headers(self, api_key: str | None = None) -> dict:
        """Retorna headers para requisições."""
        return {
            'Content-Type': 'application/json',
            'apikey': api_key or self.api_key,
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
        api_key: str | None = None,
    ) -> dict:
        """Faz requisição à Evolution API."""
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(api_key),
                    json=data,
                    params=params,
                )

                if response.status_code >= 400:
                    error_detail = response.text
                    logger.error(
                        f"Evolution API error: {response.status_code} - {error_detail}"
                    )
                    raise EvolutionAPIError(
                        f"Evolution API retornou status {response.status_code}: {error_detail}"
                    )

                return response.json()

            except httpx.TimeoutException:
                logger.error(f"Timeout na requisição para {url}")
                raise EvolutionAPIError("Timeout na conexão com Evolution API")
            except httpx.RequestError as e:
                logger.error(f"Erro de conexão com Evolution API: {e}")
                raise EvolutionAPIError(f"Erro de conexão: {str(e)}")

    def _request_sync(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
        api_key: str | None = None,
    ) -> dict:
        """Versão síncrona da requisição (para uso em tasks Celery)."""
        url = f"{self.base_url}{endpoint}"

        try:
            response = httpx.request(
                method=method,
                url=url,
                headers=self._get_headers(api_key),
                json=data,
                params=params,
                timeout=self.timeout,
            )

            if response.status_code >= 400:
                error_detail = response.text
                logger.error(
                    f"Evolution API error: {response.status_code} - {error_detail}"
                )
                raise EvolutionAPIError(
                    f"Evolution API retornou status {response.status_code}: {error_detail}"
                )

            return response.json()

        except httpx.TimeoutException:
            logger.error(f"Timeout na requisição para {url}")
            raise EvolutionAPIError("Timeout na conexão com Evolution API")
        except httpx.RequestError as e:
            logger.error(f"Erro de conexão com Evolution API: {e}")
            raise EvolutionAPIError(f"Erro de conexão: {str(e)}")

    # ==================== Gerenciamento de Instância ====================

    async def create_instance(self, instance_name: str, webhook_url: str = '') -> dict:
        """
        Cria uma nova instância do WhatsApp.

        Args:
            instance_name: Nome único da instância
            webhook_url: URL para receber webhooks

        Returns:
            Dados da instância criada
        """
        data = {
            'instanceName': instance_name,
            'qrcode': True,
            'integration': 'WHATSAPP-BAILEYS',
        }

        if webhook_url:
            data['webhook'] = webhook_url
            data['webhookByEvents'] = True
            data['events'] = [
                'QRCODE_UPDATED',
                'CONNECTION_UPDATE',
                'MESSAGES_UPSERT',
                'MESSAGES_UPDATE',
                'SEND_MESSAGE',
            ]

        result = await self._request('POST', '/instance/create', data=data)
        logger.info(f"Instância criada: {instance_name}")
        return result

    def create_instance_sync(self, instance_name: str, webhook_url: str = '', token: str = '') -> dict:
        """
        Versão síncrona de create_instance.

        Args:
            instance_name: Nome único da instância
            webhook_url: URL para receber webhooks
            token: Token customizado para a instância (opcional)
        """
        data = {
            'instanceName': instance_name,
            'qrcode': True,
            'integration': 'WHATSAPP-BAILEYS',
        }

        if webhook_url:
            data['webhook'] = webhook_url
            data['webhookByEvents'] = True
            data['events'] = [
                'QRCODE_UPDATED',
                'CONNECTION_UPDATE',
                'MESSAGES_UPSERT',
                'MESSAGES_UPDATE',
                'SEND_MESSAGE',
            ]

        if token:
            data['token'] = token

        result = self._request_sync('POST', '/instance/create', data=data)
        logger.info(f"Instância criada: {instance_name}")
        return result

    async def get_instance_status(self, instance_name: str, api_key: str | None = None) -> dict:
        """
        Obtém o status de conexão da instância.

        Returns:
            Estado da conexão (open, close, connecting)
        """
        result = await self._request(
            'GET',
            f'/instance/connectionState/{instance_name}',
            api_key=api_key
        )
        return result

    def get_instance_status_sync(self, instance_name: str, api_key: str | None = None) -> dict:
        """Versão síncrona de get_instance_status."""
        return self._request_sync(
            'GET',
            f'/instance/connectionState/{instance_name}',
            api_key=api_key
        )

    async def get_qr_code(self, instance_name: str, api_key: str | None = None) -> str:
        """
        Obtém o QR Code para conexão.

        Returns:
            QR Code em base64
        """
        result = await self._request('GET', f'/instance/connect/{instance_name}', api_key=api_key)

        if 'base64' in result:
            return result['base64']
        elif 'qrcode' in result:
            return result['qrcode'].get('base64', '')

        return ''

    def get_qr_code_sync(self, instance_name: str, api_key: str | None = None) -> str:
        """Versão síncrona de get_qr_code."""
        result = self._request_sync('GET', f'/instance/connect/{instance_name}', api_key=api_key)

        if 'base64' in result:
            return result['base64']
        elif 'qrcode' in result:
            return result['qrcode'].get('base64', '')

        return ''

    async def disconnect_instance(self, instance_name: str, api_key: str | None = None) -> bool:
        """Desconecta a instância (logout)."""
        try:
            await self._request('DELETE', f'/instance/logout/{instance_name}', api_key=api_key)
            logger.info(f"Instância desconectada: {instance_name}")
            return True
        except EvolutionAPIError:
            return False

    def disconnect_instance_sync(self, instance_name: str, api_key: str | None = None) -> bool:
        """Versão síncrona de disconnect_instance."""
        try:
            self._request_sync('DELETE', f'/instance/logout/{instance_name}', api_key=api_key)
            logger.info(f"Instância desconectada: {instance_name}")
            return True
        except EvolutionAPIError:
            return False

    async def delete_instance(self, instance_name: str) -> bool:
        """Remove a instância completamente."""
        try:
            await self._request('DELETE', f'/instance/delete/{instance_name}')
            logger.info(f"Instância removida: {instance_name}")
            return True
        except EvolutionAPIError:
            return False

    def delete_instance_sync(self, instance_name: str) -> bool:
        """Versão síncrona de delete_instance."""
        try:
            self._request_sync('DELETE', f'/instance/delete/{instance_name}')
            logger.info(f"Instância removida: {instance_name}")
            return True
        except EvolutionAPIError:
            return False

    # ==================== Configuração de Webhook ====================

    async def set_webhook(self, instance_name: str, webhook_url: str, api_key: str | None = None) -> bool:
        """Configura o webhook da instância."""
        data = {
            'url': webhook_url,
            'webhookByEvents': True,
            'events': [
                'QRCODE_UPDATED',
                'CONNECTION_UPDATE',
                'MESSAGES_UPSERT',
                'MESSAGES_UPDATE',
                'SEND_MESSAGE',
            ]
        }

        await self._request('POST', f'/webhook/set/{instance_name}', data=data, api_key=api_key)
        logger.info(f"Webhook configurado para {instance_name}: {webhook_url}")
        return True

    def set_webhook_sync(self, instance_name: str, webhook_url: str, api_key: str | None = None) -> bool:
        """Versão síncrona de set_webhook."""
        data = {
            'url': webhook_url,
            'webhookByEvents': True,
            'events': [
                'QRCODE_UPDATED',
                'CONNECTION_UPDATE',
                'MESSAGES_UPSERT',
                'MESSAGES_UPDATE',
                'SEND_MESSAGE',
            ]
        }

        self._request_sync('POST', f'/webhook/set/{instance_name}', data=data, api_key=api_key)
        logger.info(f"Webhook configurado para {instance_name}: {webhook_url}")
        return True

    # ==================== Envio de Mensagens ====================

    async def send_text(
        self,
        instance_name: str,
        phone: str,
        text: str,
        api_key: str | None = None,
    ) -> dict:
        """
        Envia uma mensagem de texto.

        Args:
            instance_name: Nome da instância
            phone: Número do destinatário (formato: 5511999999999)
            text: Texto da mensagem
            api_key: Chave de API específica da instância (opcional)

        Returns:
            Dados da mensagem enviada (inclui ID)
        """
        # Formata o número (remove caracteres especiais, adiciona @s.whatsapp.net)
        phone_formatted = self._format_phone(phone)

        data = {
            'number': phone_formatted,
            'text': text
        }

        result = await self._request(
            'POST',
            f'/message/sendText/{instance_name}',
            data=data,
            api_key=api_key
        )

        logger.info(f"Mensagem enviada para {phone} via {instance_name}")
        return result

    def send_text_sync(
        self,
        instance_name: str,
        phone: str,
        text: str,
        api_key: str | None = None,
    ) -> dict:
        """Versão síncrona de send_text."""
        phone_formatted = self._format_phone(phone)

        data = {
            'number': phone_formatted,
            'text': text
        }

        result = self._request_sync(
            'POST',
            f'/message/sendText/{instance_name}',
            data=data,
            api_key=api_key
        )

        logger.info(f"Mensagem enviada para {phone} via {instance_name}")
        return result

    async def send_media(
        self,
        instance_name: str,
        phone: str,
        media_url: str,
        media_type: str,
        caption: str = '',
        filename: str = '',
    ) -> dict:
        """
        Envia uma mensagem com mídia.

        Args:
            instance_name: Nome da instância
            phone: Número do destinatário
            media_url: URL da mídia
            media_type: Tipo (image, document, audio, video)
            caption: Legenda (opcional)
            filename: Nome do arquivo (para documentos)

        Returns:
            Dados da mensagem enviada
        """
        phone_formatted = self._format_phone(phone)

        data = {
            'number': phone_formatted,
            'mediaMessage': {
                'mediatype': media_type,
                'media': media_url,
            }
        }

        if caption:
            data['mediaMessage']['caption'] = caption
        if filename:
            data['mediaMessage']['fileName'] = filename

        result = await self._request(
            'POST',
            f'/message/sendMedia/{instance_name}',
            data=data
        )

        logger.info(f"Mídia enviada para {phone} via {instance_name}")
        return result

    def send_media_sync(
        self,
        instance_name: str,
        phone: str,
        media_url: str,
        media_type: str,
        caption: str = '',
        filename: str = '',
        api_key: str | None = None,
    ) -> dict:
        """Versão síncrona de send_media."""
        phone_formatted = self._format_phone(phone)

        data = {
            'number': phone_formatted,
            'mediaMessage': {
                'mediatype': media_type,
                'media': media_url,
            }
        }

        if caption:
            data['mediaMessage']['caption'] = caption
        if filename:
            data['mediaMessage']['fileName'] = filename

        result = self._request_sync(
            'POST',
            f'/message/sendMedia/{instance_name}',
            data=data,
            api_key=api_key
        )

        logger.info(f"Mídia enviada para {phone} via {instance_name}")
        return result

    # ==================== Health Check ====================

    async def health_check(self, instance_name: str) -> bool:
        """Verifica se a instância está conectada e saudável."""
        try:
            status = await self.get_instance_status(instance_name)
            state = status.get('state', status.get('instance', {}).get('state', ''))
            return state.lower() == 'open'
        except EvolutionAPIError:
            return False

    def health_check_sync(self, instance_name: str) -> bool:
        """Versão síncrona de health_check."""
        try:
            status = self.get_instance_status_sync(instance_name)
            state = status.get('state', status.get('instance', {}).get('state', ''))
            return state.lower() == 'open'
        except EvolutionAPIError:
            return False

    # ==================== Utilitários ====================

    def _format_phone(self, phone: str) -> str:
        """
        Formata número de telefone para o padrão da Evolution API.

        Remove caracteres especiais e garante formato correto.
        """
        import re

        # Remove tudo que não é dígito
        phone_clean = re.sub(r'\D', '', phone)

        # Remove 55 do início se já tiver (para evitar duplicação)
        if phone_clean.startswith('55') and len(phone_clean) > 11:
            phone_clean = phone_clean[2:]

        # Adiciona 55 se não tiver
        if not phone_clean.startswith('55'):
            phone_clean = f'55{phone_clean}'

        return phone_clean


# Instância global do serviço
whatsapp_service = WhatsAppService()
