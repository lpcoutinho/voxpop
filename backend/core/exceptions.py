"""
Custom exceptions and exception handler for VoxPop.
"""
import logging

from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class VoxPopException(APIException):
    """Base exception for VoxPop."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Ocorreu um erro.'
    default_code = 'error'


class PlanLimitExceeded(VoxPopException):
    """Raised when a plan limit is exceeded."""
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = 'Limite do plano excedido.'
    default_code = 'plan_limit_exceeded'


class RateLimitExceeded(VoxPopException):
    """Raised when rate limit is exceeded."""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Limite de requisicoes excedido.'
    default_code = 'rate_limit_exceeded'


class WhatsAppConnectionError(VoxPopException):
    """Raised when WhatsApp connection fails."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Erro de conexao com WhatsApp.'
    default_code = 'whatsapp_connection_error'


class EvolutionAPIError(VoxPopException):
    """Raised when Evolution API returns an error."""
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'Erro na comunicacao com Evolution API.'
    default_code = 'evolution_api_error'


class CampaignError(VoxPopException):
    """Raised for campaign-related errors."""
    default_detail = 'Erro na campanha.'
    default_code = 'campaign_error'


class MessageDeliveryError(VoxPopException):
    """Raised when message delivery fails."""
    default_detail = 'Erro no envio da mensagem.'
    default_code = 'message_delivery_error'


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    """
    # Handle Django exceptions
    if isinstance(exc, Http404):
        exc = VoxPopException(
            detail='Recurso nao encontrado.',
            code='not_found'
        )
        exc.status_code = status.HTTP_404_NOT_FOUND

    elif isinstance(exc, PermissionDenied):
        exc = VoxPopException(
            detail='Voce nao tem permissao para esta acao.',
            code='permission_denied'
        )
        exc.status_code = status.HTTP_403_FORBIDDEN

    elif isinstance(exc, DjangoValidationError):
        exc = VoxPopException(
            detail=exc.messages if hasattr(exc, 'messages') else str(exc),
            code='validation_error'
        )

    # Call REST framework's default exception handler
    response = exception_handler(exc, context)

    if response is not None:
        # Add custom fields to response
        error_data = {
            'error': True,
            'code': getattr(exc, 'default_code', 'error'),
            'message': response.data.get('detail', str(exc)),
        }

        # Include field errors for validation errors
        if hasattr(response.data, 'items'):
            field_errors = {
                k: v for k, v in response.data.items()
                if k != 'detail'
            }
            if field_errors:
                error_data['fields'] = field_errors

        response.data = error_data

        # Log server errors
        if response.status_code >= 500:
            logger.error(
                f"Server error: {exc}",
                exc_info=True,
                extra={'context': context}
            )

    return response
