"""
Serviço para gerenciar secrets de webhooks.
"""
import logging
from typing import Optional
from django.core.cache import cache
from apps.whatsapp.models import WebhookSecret, WebhookSecretUsage

logger = logging.getLogger(__name__)


class WebhookSecretService:
    """
    Serviço para gerenciar secrets de webhooks.
    """

    def get_active_secret(self, session_name: str) -> Optional[WebhookSecret]:
        """
        Retorna o secret ativo para uma sessão.
        Usa cache para performance.
        """
        cache_key = f'webhook_secret:{session_name}'

        # Tenta buscar do cache primeiro
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
                # Salva no cache
                cache.set(cache_key, secret, timeout=300)  # 5 minutos
                return secret
        except Exception as e:
            logger.error(f"Erro ao buscar secret para {session_name}: {e}")

        logger.warning(f"Nenhum secret ativo encontrado para {session_name}")

    def get_all_secrets(self) -> list[WebhookSecret]:
        """Retorna todos os secrets (para debug)."""
        return list(WebhookSecret.objects.filter(is_active=True).select_related('tenant'))

    def create_secret(
        self,
        tenant_id: int,
        name: str,
        description: Optional[str] = None,
        secret_token: str,
        webhook_url: Optional[str] = None
    ) -> WebhookSecret:
        """
        Cria um novo secret para uma instância.
        """
        from apps.tenants.models import Client
        from apps.tenants.utils import get_tenant_by_id

        tenant = get_tenant_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} não encontrado")

        secret = WebhookSecret.objects.create(
            tenant=tenant,
            name=name,
            description=description,
            secret_token=secret_token,
            webhook_url=webhook_url,
            is_active=True,
        )

        logger.info(f"Secret criado para {name}: {secret.secret_token[:8]}...")

        # Limpa cache para forçar nova busca
        cache.delete_many([f"webhook_secret:{name}" for name in [name]])

        return secret

    def rotate_secret(self, secret: WebhookSecret) -> WebhookSecret:
        """
        Rotaciona um secret: marca o atual como inativo e cria um novo.
        """
        from apps.tenants.utils import get_tenant_by_id

        tenant = secret.tenant

        # Marca secret atual como inativo
        secret.is_active = False
        secret.save()

        # Cria novo secret
        new_secret = WebhookSecret.objects.create(
            tenant=tenant,
            name=secret.name,
            description=secret.description,
            secret_token=secret.secret_token,  # Será o mesmo token por enquanto durar a rotação
            webhook_url=secret.webhook_url,
            is_active=True,
        )

        logger.info(f"Secret rotacionado para {tenant.schema_name}: {old_secret.secret_token[:8]}... -> {new_secret.secret_token[:8]}...")

        # Limpa cache
        cache.delete(f"webhook_secret:{secret.name}")

        return new_secret

    def deactivate_secret(self, secret: WebhookSecret) -> WebhookSecret:
        """
        Desativa um secret sem deletar (para manter histórico).
        """
        secret.is_active = False
        secret.save()

        logger.info(f"Secret desativado para {secret.name}")

    def delete_secret(self, secret: WebhookSecret) -> bool:
        """
        Deleta um secret permanentemente.
        """
        secret.delete()
        return True


# Singleton instance
webhook_secret_service = WebhookSecretService()
