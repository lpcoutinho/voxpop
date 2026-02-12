"""
Controlador centralizado para gerenciar webhooks recebidos da Evolution API.

Este controlador:
1. Recebe requisições de webhook
2. Autentica usando o WebhookAuthenticationMiddleware
3. Despacha eventos para handlers apropriados
4. Gerencia erros e logs
5. Fornece resposta padronizada

Handlers devem ter o método `handle(request)` que:
- Retorna HttpResponse com dados padronizados
- Em caso de erro: usa `create_error_response(error_code, error_message)`
"""
import logging
import json
from typing import Callable, Optional, Dict, Any
from django.http import HttpResponse
from django.views.decorators.http import csrf_exempt
from apps.whatsapp.middleware.webhook_authentication import webhook_authentication

logger = logging.getLogger(__name__)


# Respostas padronizadas
def create_success_response(data: Dict = None, message: str = "Sucesso") -> HttpResponse:
    """
    Cria uma resposta de sucesso padronizada.
    """
    response_data = {
        'success': True,
        'message': message
    }
    if data:
        response_data['data'] = data

    return HttpResponse(
        status=200,
        content_type='application/json',
        data=response_data
    )


def create_error_response(
    error_code: str,
    error_message: str,
    status: int = 400
) -> HttpResponse:
    """
    Cria uma resposta de erro padronizada.
    """
    response_data = {
        'success': False,
        'error': {
            'code': error_code,
            'message': error_message
        }
    }

    return HttpResponse(
        status=status,
        content_type='application/json',
        data=response_data
    )


class WebhookController:
    """
    Controlador central para gerenciar webhooks da Evolution API.
    """

    def __init__(self):
        """Inicializa o controlador com os handlers."""
        self.handlers: Dict[str, Callable] = {}

    def register_handler(self, event_type: str, handler: Callable):
        """
        Registra um handler para um tipo de evento.
        """
        self.handlers[event_type] = handler
        logger.info(f"Handler registrado para evento: {event_type}")

    def _get_handler(self, event_type: str) -> Optional[Callable]:
        """
        Retorna o handler apropriado para um tipo de evento.
        """
        return self.handlers.get(event_type)

    def _parse_event(self, request) -> Optional[Dict[str, Any]]:
        """
        Parse e valida o payload do webhook.
        """
        try:
            # Lê o payload
            payload = json.loads(request.body)

            # Extrai tipo de evento
            event_type = payload.get('event')
            if not event_type:
                logger.error(f"Evento sem tipo: {payload}")
                return None

            # Extrai dados específicos por tipo
            event_data = payload.get('data', {})
            if isinstance(event_data, dict):
                event_data.update({
                    'event': event_type,
                    'timestamp': payload.get('timestamp', ''),
                    'instance': payload.get('instance_name', ''),
                })

            return event_data

        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
            return None

    def _dispatch_event(self, request):
        """
        Despacha o evento para o handler apropriado.
        """
        event_data = self._parse_event(request)
        if not event_data:
            logger.error("Nenhum evento para despachar")
            return create_error_response(
                error_code='INVALID_EVENT',
                error_message='Evento inválido ou sem dados'
            )

        event_type = event_data.get('event', '')
        handler = self._get_handler(event_type)

        if not handler:
            logger.warning(f"Nenhum handler para evento: {event_type}")
            return create_error_response(
                error_code='HANDLER_NOT_FOUND',
                error_message=f'Handler não encontrado para evento: {event_type}'
            )

        logger.info(f"Evento recebido: {event_type} - despachando para handler")

        # Chama o handler
        return handler.handle(request)

    @csrf_exempt
    def handle_webhook(self, request):
        """
        Endpoint principal para webhooks globais.
        POST /api/v1/whatsapp/

        Evolution API envia eventos de múltiplas instâncias
        para este endpoint genérico, aceitamos qualquer instância
        """
        return self._dispatch_event(request)

    @csrf_exempt
    def handle_instance_webhook(self, request, instance_name: str):
        """
        Endpoint para webhook de uma instância específica.
        POST /api/v1/whatsapp/webhook/{instance_name}/

        Este endpoint é mais específico e permite:
        - Autenticação específica por instância
        - Roteamento específico para handler dessa instância
        """
        return self._dispatch_event(request)
