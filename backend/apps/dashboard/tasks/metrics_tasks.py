"""
Celery tasks for dashboard metrics calculation.
"""
import logging
from datetime import date, timedelta

from celery import shared_task
from django.db.models import Count, Q
from django.utils import timezone
from tenant_schemas_celery.task import TenantTask

logger = logging.getLogger(__name__)


@shared_task(bind=True, base=TenantTask, queue='analytics')
def calculate_daily_metrics_task(self, date_str: str) -> None:
    """
    Calcula métricas do dia especificado.

    Args:
        date_str: Data no formato 'YYYY-MM-DD'
    """
    from apps.dashboard.models import DailyMetrics
    from apps.supporters.models import Supporter
    from apps.messaging.models import Message
    from apps.campaigns.models import Campaign

    target_date = date.fromisoformat(date_str)

    logger.info(f"Calculando métricas para {target_date}")

    # Início e fim do dia
    day_start = timezone.make_aware(
        timezone.datetime.combine(target_date, timezone.datetime.min.time())
    )
    day_end = day_start + timedelta(days=1)

    # Novos apoiadores
    new_supporters = Supporter.objects.filter(
        created_at__gte=day_start,
        created_at__lt=day_end
    ).count()

    # Total de apoiadores até o fim do dia
    total_supporters = Supporter.objects.filter(
        created_at__lt=day_end
    ).count()

    # Mensagens do dia
    messages_qs = Message.objects.filter(
        created_at__gte=day_start,
        created_at__lt=day_end
    )

    messages_sent = messages_qs.filter(
        status__in=[Message.Status.SENT, Message.Status.DELIVERED, Message.Status.READ]
    ).count()

    messages_delivered = messages_qs.filter(
        status__in=[Message.Status.DELIVERED, Message.Status.READ]
    ).count()

    messages_read = messages_qs.filter(
        status=Message.Status.READ
    ).count()

    messages_failed = messages_qs.filter(
        status=Message.Status.FAILED
    ).count()

    # Campanhas
    campaigns_created = Campaign.objects.filter(
        created_at__gte=day_start,
        created_at__lt=day_end
    ).count()

    campaigns_completed = Campaign.objects.filter(
        completed_at__gte=day_start,
        completed_at__lt=day_end,
        status=Campaign.Status.COMPLETED
    ).count()

    # Atualiza ou cria métricas do dia
    metrics, created = DailyMetrics.objects.update_or_create(
        date=target_date,
        defaults={
            'new_supporters': new_supporters,
            'total_supporters': total_supporters,
            'messages_sent': messages_sent,
            'messages_delivered': messages_delivered,
            'messages_read': messages_read,
            'messages_failed': messages_failed,
            'campaigns_created': campaigns_created,
            'campaigns_completed': campaigns_completed,
        }
    )

    action = "criadas" if created else "atualizadas"
    logger.info(f"Métricas {action} para {target_date}")


@shared_task(bind=True, base=TenantTask, queue='analytics')
def update_campaign_metrics(self, campaign_id: int) -> None:
    """
    Atualiza métricas de uma campanha específica.

    Args:
        campaign_id: ID da campanha
    """
    from apps.campaigns.models import Campaign
    from apps.dashboard.models import CampaignMetrics

    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        logger.error(f"Campanha {campaign_id} não encontrada")
        return

    # Obtém ou cria métricas
    metrics, _ = CampaignMetrics.objects.get_or_create(campaign=campaign)

    # Sincroniza e calcula
    metrics.sync_from_campaign()
    metrics.calculate_avg_delivery_time()
    metrics.save()

    logger.info(f"Métricas atualizadas para campanha {campaign.name}")


@shared_task(queue='analytics')
def calculate_all_tenants_daily_metrics() -> None:
    """
    Calcula métricas diárias para todos os tenants.
    Deve ser executada via Celery Beat às 00:05.
    """
    from django_tenants.utils import tenant_context
    from apps.tenants.models import Client

    yesterday = (timezone.now() - timedelta(days=1)).date().isoformat()

    for tenant in Client.objects.filter(is_active=True):
        try:
            with tenant_context(tenant):
                calculate_daily_metrics_task.delay(yesterday)
            logger.info(f"Métricas enfileiradas para tenant {tenant.name}")
        except Exception as e:
            logger.exception(f"Erro ao enfileirar métricas para {tenant.name}: {e}")


@shared_task(bind=True, base=TenantTask, queue='analytics')
def recalculate_metrics_range(self, start_date: str, end_date: str) -> None:
    """
    Recalcula métricas para um período.

    Args:
        start_date: Data inicial (YYYY-MM-DD)
        end_date: Data final (YYYY-MM-DD)
    """
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    current = start
    while current <= end:
        calculate_daily_metrics_task.delay(current.isoformat())
        current += timedelta(days=1)

    logger.info(f"Recálculo enfileirado para período {start_date} a {end_date}")
