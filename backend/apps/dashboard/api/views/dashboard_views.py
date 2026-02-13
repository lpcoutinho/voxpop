"""
ViewSet for Dashboard metrics.
"""
from datetime import date, timedelta

from django.db.models import Sum, Count
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.dashboard.api.serializers import MetricsQuerySerializer
from apps.supporters.models import Supporter
from apps.campaigns.models import Campaign, CampaignItem
from apps.whatsapp.models import WhatsAppSession
from core.permissions import IsTenantMember


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for dashboard metrics.

    list: GET /api/v1/dashboard/ - Returns dashboard stats
    metrics: GET /api/v1/dashboard/metrics/?start=YYYY-MM-DD&end=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated, IsTenantMember]

    def list(self, request):
        """
        Get dashboard overview cards.
        GET /api/v1/dashboard/
        """
        today = timezone.now().date()
        month_start = today.replace(day=1)

        # Supporters stats (soft-deleted are automatically excluded by manager)
        total_supporters = Supporter.objects.count()
        new_supporters_today = Supporter.objects.filter(
            created_at__date=today
        ).count()

        # Messages stats - usar CampaignItem que é a fonte de verdade
        messages_sent_month = CampaignItem.objects.filter(
            sent_at__date__gte=month_start,
            status__in=[CampaignItem.Status.SENT, CampaignItem.Status.DELIVERED, CampaignItem.Status.READ]
        ).count()

        messages_sent_today = CampaignItem.objects.filter(
            sent_at__date=today,
            status__in=[CampaignItem.Status.SENT, CampaignItem.Status.DELIVERED, CampaignItem.Status.READ]
        ).count()

        # Calculate delivery and read rates from this month
        month_items = CampaignItem.objects.filter(sent_at__date__gte=month_start)
        total_sent = month_items.filter(
            status__in=[CampaignItem.Status.SENT, CampaignItem.Status.DELIVERED, CampaignItem.Status.READ]
        ).count()

        if total_sent > 0:
            delivered = month_items.filter(
                status__in=[CampaignItem.Status.DELIVERED, CampaignItem.Status.READ]
            ).count()
            read = month_items.filter(status=CampaignItem.Status.READ).count()
            delivery_rate = (delivered / total_sent) * 100
            read_rate = (read / total_sent) * 100
        else:
            delivery_rate = 0.0
            read_rate = 0.0

        # Total messages from campaign counters
        total_messages_delivered = Campaign.objects.aggregate(
            total=Sum('messages_delivered')
        )['total'] or 0
        total_messages_read = Campaign.objects.aggregate(
            total=Sum('messages_read')
        )['total'] or 0
        total_messages_failed = Campaign.objects.aggregate(
            total=Sum('messages_failed')
        )['total'] or 0

        # Total campaigns
        total_campaigns = Campaign.objects.count()

        # Active campaigns (soft-deleted are automatically excluded by manager)
        active_campaigns = Campaign.objects.filter(
            status__in=[Campaign.Status.RUNNING, Campaign.Status.SCHEDULED]
        ).count()

        # WhatsApp sessions
        total_sessions = WhatsAppSession.objects.filter(is_active=True).count()
        connected_sessions = WhatsAppSession.objects.filter(
            is_active=True,
            status=WhatsAppSession.Status.CONNECTED
        ).count()

        data = {
            'total_supporters': total_supporters,
            'total_campaigns': total_campaigns,
            'active_campaigns': active_campaigns,
            'messages_sent': messages_sent_month,  # Usar messages_sent para compatibilidade com frontend
            'messages_delivered': total_messages_delivered,
            'messages_read': total_messages_read,
            'messages_failed': total_messages_failed,
            'delivery_rate': round(delivery_rate, 1),
            'read_rate': round(read_rate, 1),
            'whatsapp_sessions': {
                'connected': connected_sessions,
                'total': total_sessions
            }
        }

        return Response(data)

    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """
        Get daily metrics for a date range.
        GET /api/v1/dashboard/metrics/?start=YYYY-MM-DD&end=YYYY-MM-DD
        """
        serializer = MetricsQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        start_date = serializer.validated_data['start']
        end_date = serializer.validated_data['end']

        # Calcular métricas em tempo real para cada dia no período
        from datetime import timedelta
        import collections

        metrics_data = []
        current_date = start_date

        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)

            # Contar mensagens do dia usando CampaignItem
            items_day = CampaignItem.objects.filter(
                sent_at__date=current_date
            )

            sent = items_day.filter(
                status__in=[CampaignItem.Status.SENT, CampaignItem.Status.DELIVERED, CampaignItem.Status.READ]
            ).count()

            delivered = items_day.filter(
                status__in=[CampaignItem.Status.DELIVERED, CampaignItem.Status.READ]
            ).count()

            read = items_day.filter(status=CampaignItem.Status.READ).count()

            failed = items_day.filter(status=CampaignItem.Status.FAILED).count()

            metrics_data.append({
                'date': current_date.isoformat(),
                'sent': sent,
                'delivered': delivered,
                'read': read,
                'failed': failed,
            })

            current_date = next_date

        return Response(metrics_data)

    @action(detail=False, methods=['get'])
    def top_campaigns(self, request):
        """
        Get top campaigns by engagement.
        GET /api/v1/dashboard/top_campaigns/
        """
        # Get campaigns from last 30 days with engagement
        thirty_days_ago = timezone.now() - timedelta(days=30)

        campaigns = Campaign.objects.filter(
            started_at__gte=thirty_days_ago
        ).exclude(
            total_recipients=0
        ).order_by('-messages_read')[:5]

        data = []
        for campaign in campaigns:
            read_rate = 0.0
            if campaign.total_recipients > 0:
                read_rate = round((campaign.messages_read / campaign.total_recipients) * 100, 1)

            data.append({
                'id': campaign.id,
                'name': campaign.name,
                'total_recipients': campaign.total_recipients,
                'sent': campaign.messages_sent,
                'delivered': campaign.messages_delivered,
                'read': campaign.messages_read,
                'read_rate': read_rate
            })

        return Response(data)

    @action(detail=False, methods=['get'])
    def message_status(self, request):
        """
        Get message status distribution.
        GET /api/v1/dashboard/message_status/
        """
        # Get stats from CampaignItem (fonte de verdade)
        stats = CampaignItem.objects.values('status').annotate(
            count=Count('id')
        )

        # Convert to dict
        status_map = {
            'sent': 0,
            'delivered': 0,
            'read': 0,
            'failed': 0,
            'pending': 0
        }

        for stat in stats:
            status = stat['status']
            if status in status_map:
                status_map[status] = stat['count']
            elif status in ['queued', 'pending']:
                status_map['pending'] += stat['count']

        return Response(status_map)

    @action(detail=False, methods=['get'], url_path='activities')
    def activities(self, request):
        """
        Get recent activities.
        GET /api/v1/dashboard/activities/?limit=5
        """
        limit = int(request.query_params.get('limit', 5))

        # Get recent campaigns as activities
        recent_campaigns = Campaign.objects.filter(
            started_at__isnull=False
        ).order_by('-started_at')[:limit]

        activities = []
        for campaign in recent_campaigns:
            activities.append({
                'id': campaign.id,
                'type': 'campaign',
                'title': f"Campanha '{campaign.name}' foi iniciada",
                'time': self._format_time_ago(campaign.started_at),
                'status': campaign.status if campaign.status != 'completed' else None
            })

        return Response(activities)

    def _format_time_ago(self, dt):
        """Format datetime as 'X time ago' string."""
        from django.utils.timesince import timesince
        return f"{timesince(dt)} atrás"
