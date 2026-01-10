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

from apps.dashboard.models import DailyMetrics
from apps.dashboard.api.serializers import (
    OverviewSerializer,
    DailyMetricsSerializer,
    MetricsQuerySerializer,
)
from apps.supporters.models import Supporter
from apps.messaging.models import Message
from apps.campaigns.models import Campaign
from apps.whatsapp.models import WhatsAppSession
from core.permissions import IsTenantMember


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for dashboard metrics.

    overview: GET /api/v1/dashboard/overview/
    metrics: GET /api/v1/dashboard/metrics/?start=YYYY-MM-DD&end=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated, IsTenantMember]

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        Get dashboard overview cards.
        GET /api/v1/dashboard/overview/
        """
        today = timezone.now().date()
        month_start = today.replace(day=1)

        # Supporters stats (soft-deleted are automatically excluded by manager)
        total_supporters = Supporter.objects.count()
        new_supporters_today = Supporter.objects.filter(
            created_at__date=today
        ).count()

        # Messages stats
        messages_sent_month = Message.objects.filter(
            created_at__date__gte=month_start,
            status__in=[Message.Status.SENT, Message.Status.DELIVERED, Message.Status.READ]
        ).count()

        messages_sent_today = Message.objects.filter(
            created_at__date=today,
            status__in=[Message.Status.SENT, Message.Status.DELIVERED, Message.Status.READ]
        ).count()

        # Calculate delivery and read rates from this month
        month_messages = Message.objects.filter(created_at__date__gte=month_start)
        total_sent = month_messages.filter(
            status__in=[Message.Status.SENT, Message.Status.DELIVERED, Message.Status.READ]
        ).count()

        if total_sent > 0:
            delivered = month_messages.filter(
                status__in=[Message.Status.DELIVERED, Message.Status.READ]
            ).count()
            read = month_messages.filter(status=Message.Status.READ).count()
            delivery_rate = (delivered / total_sent) * 100
            read_rate = (read / total_sent) * 100
        else:
            delivery_rate = 0.0
            read_rate = 0.0

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
            'new_supporters_today': new_supporters_today,
            'messages_sent_month': messages_sent_month,
            'messages_sent_today': messages_sent_today,
            'delivery_rate': round(delivery_rate, 1),
            'read_rate': round(read_rate, 1),
            'active_campaigns': active_campaigns,
            'whatsapp_sessions': {
                'connected': connected_sessions,
                'total': total_sessions
            }
        }

        return Response(OverviewSerializer(data).data)

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

        metrics = DailyMetrics.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')

        return Response(DailyMetricsSerializer(metrics, many=True).data)

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
        ).order_by('-read_count')[:5]

        data = []
        for campaign in campaigns:
            data.append({
                'id': campaign.id,
                'name': campaign.name,
                'total_recipients': campaign.total_recipients,
                'sent': campaign.sent_count,
                'delivered': campaign.delivered_count,
                'read': campaign.read_count,
                'read_rate': campaign.read_rate
            })

        return Response(data)

    @action(detail=False, methods=['get'])
    def message_status(self, request):
        """
        Get message status distribution.
        GET /api/v1/dashboard/message_status/
        """
        # Get stats from last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)

        stats = Message.objects.filter(
            created_at__gte=thirty_days_ago
        ).values('status').annotate(
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
            elif status in ['queued']:
                status_map['pending'] += stat['count']

        return Response(status_map)
