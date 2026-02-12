"""
Middleware de autenticação para webhooks da Evolution API.
Valida assinaturas HMAC-SHA256 dos webhooks recebidos.

Processo de Webhooks:
1. Recebe webhook do Evolution API
2. Valida assinatura HMAC-SHA256
3. Adiciona contexto de autenticação ao request
4. Chama handler apropriado
"""
import logging
import hmac
import hashlib
from django.utils import timezone
from django.core.cache import cache
from apps.whatsapp.models import WebhookSecret

logger = logging.getLogger(__name__)


# Constantes
EVOLUTION_WEBHOOK_SIGNATURE_HEADER = 'Evolution-Webhook-Signature'
EVOLUTION_WEBHOOK_TIMESTAMP_HEADER = 'Evolution-Webhook-Timestamp'
EVOLUTION_WEBHOOK_API_KEY_HEADER = 'Evolution-Api-Key'


class WebhookAuthenticationMiddleware:
    """
    Middleware para autenticar requisições de webhook da Evolution API.

    Evolution API envia cabeçalhos:
    - X-Evolution-Webhook-Signature: HMAC-SHA256 do payload
    - X-Evolution-Webhook-Timestamp: Timestamp do evento
    - Evolution-Api-Key: API Key da instância (usado para validação extra)

    Este middleware:
    1. Verifica se o endpoint é um webhook
    2. Busca o secret ativo para a sessão
    3. Extrai e valida a assinatura
    4. Verifica a API key (opcional)
    5. Adiciona contexto de autenticação ao request
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _get_webhook_secret(self, session_name: str) -> Optional[WebhookSecret]:
        """
        Busca o secret ativo para uma sessão.
        Usa cache para performance.
        """
        cache_key = f'webhook_secret:{session_name}'

        # Tenta do cache primeiro
        secret = cache.get(cache_key)
        if secret:
            # Verifica se o secret ainda é válido (não expirado)
            if secret.is_active and not secret.is_expired:
                return secret

        # Se não está no cache ou expirou, busca do banco
        try:
            secret = WebhookSecret.objects.filter(
                name=session_name,
                is_active=True
            ).select_related('tenant').order_by('-created_at').first()

            if secret:
                cache.set(cache_key, secret, timeout=300)
                return secret

        except Exception as e:
            logger.error(f"Erro ao buscar secret para {session_name}: {e}")

        return None

    def _validate_signature(self, request, session_name: str, payload: bytes, timestamp: str, api_key: str) -> tuple[bool, str]:
        """
        Valida a assinatura HMAC-SHA256 do webhook.
        """
        secret = self._get_webhook_secret(session_name)
        if not secret:
            return False, "Secret não encontrado"

        # Extrai a assinatura esperada
        received_signature = request.META.get(EVOLUTION_WEBHOOK_SIGNATURE_HEADER)
        if not received_signature:
            return False, "Assinatura não encontrada"

        # Decodifica a assinatura (hex)
        try:
            expected_signature = hmac.new(
                secret.secret_token.encode('utf-8'),
                payload,
                digestmod='sha256'
            ).hexdigest()
        except Exception as e:
            logger.error(f"Erro ao calcular assinatura esperada: {e}")
            return False, f"Erro ao calcular assinatura: {e}"

        # Compara assinaturas
        is_valid = hmac.compare_digest(
            expected_signature.encode('utf-8'),
            received_signature.encode('utf-8')
        )

        if not is_valid:
            logger.warning(f"Assinatura inválida para {session_name}")
            return False, "Assinatura inválida"

        # Verifica timestamp (replay attack protection)
        received_timestamp = request.META.get(EVOLUTION_WEBHOOK_TIMESTAMP_HEADER)
        if not received_timestamp:
            return False, "Timestamp muito antigo"

        try:
            received_ts = float(received_timestamp)
            expected_ts = float(timestamp)

            # Considera válido se estiver dentro de 5 minutos
            time_diff = abs(received_ts - expected_ts)
            if time_diff > 300:  # 5 minutos
                return False, f"Timestamp muito antigo: {time_diff}s"
        except ValueError:
            return False, "Timestamp inválido"

        # Verifica API key (opcional)
        received_api_key = request.META.get(EVOLUTION_WEBHOOK_API_KEY_HEADER)
        if received_api_key:
            if received_api_key != secret.secret_token:
                return False, "API Key inválida"

        return True, "Autenticado"

    def _is_webhook_request(self, path: str) -> bool:
        """
        Verifica se o path é um endpoint de webhook.
        """
        webhook_endpoints = [
            '/api/v1/whatsapp/webhook/',
            '/api/v1/whatsapp/webhook/<str:instance_name>/',
        ]

        return any(path.startswith(webhook_endpoint) for webhook_endpoint in webhook_endpoints)

    def process_request(self, request, session_name: str, handler):
        """
        Processa a requisição com autenticação de webhook.
        """
        # Lê o payload raw
        try:
            payload = request.body
        except Exception as e:
            return handler.create_error_response(
                error_code='INVALID_PAYLOAD',
                error_message=f"Erro ao ler payload: {e}"
            )

        # Valida autenticação
        is_authenticated, message = self._validate_signature(
            request=request,
            session_name=session_name,
            payload=payload,
            timestamp=request.META.get(EVOLUTION_WEBHOOK_TIMESTAMP_HEADER, ''),
            api_key=request.META.get(EVOLUTION_WEBHOOK_API_KEY_HEADER, '')
        )

        if not is_authenticated:
            logger.warning(f"Webhook não autenticado para {session_name}")
            return handler.create_error_response(
                error_code='AUTHENTICATION_FAILED',
                error_message=message
            )

        # Adiciona contexto de autenticação ao request
        request.authenticated_webhook_secret = secret
        request.authenticated_webhook_session_name = session_name

        logger.info(f"Webhook autenticado para {session_name}: {request.META.get(EVOLUTION_WEBHOOK_SIGNATURE_HEADER)}")

        # Chama o handler
        return handler.handle(request)

    def __call__(self, request):
        """
        Entrypoint do middleware.
        """
        # Verifica se é uma requisição de webhook
        if not self._is_webhook_request(request.path):
            return self.get_response(request)

        # Extrai nome da sessão do path
        # URLs de webhook seguem o padrão:
        # /api/v1/whatsapp/webhook/ -> sem nome específico (global)
        # /api/v1/whatsapp/webhook/<instance_name>/ -> para sessão específica

        session_name = None
        path_parts = request.path.strip('/').split('/')

        if len(path_parts) >= 4 and path_parts[1] == 'api' and path_parts[2] == 'v1' and path_parts[3] == 'whatsapp' and path_parts[4] == 'webhook':
            # Webhook global
            session_name = 'default'
        elif len(path_parts) >= 5 and path_parts[1] == 'api' and path_parts[2] == 'v1' and path_parts[3] == 'whatsapp' and path_parts[4] == 'webhook':
            # Webhook de instância específica
            session_name = path_parts[4]
        else:
            return self.get_response(request)

        # Processa a requisição
        return self.process_request(request, session_name)


def webhook_authentication(get_response):
    """
    Fábrica para criar o middleware com a função get_response.
    """
    def middleware(get_response):
        def wrapper(request):
            return WebhookAuthenticationMiddleware(get_response)
        return wrapper
