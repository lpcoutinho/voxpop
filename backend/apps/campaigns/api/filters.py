"""
Filters for Campaigns API.
"""
import django_filters

from apps.campaigns.models import Campaign


class CampaignFilter(django_filters.FilterSet):
    """Filter for Campaign list endpoint."""

    status = django_filters.ChoiceFilter(choices=Campaign.Status.choices)
    campaign_type = django_filters.ChoiceFilter(choices=Campaign.Type.choices)

    # Date range filters
    created_at_after = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_at_before = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    started_at_after = django_filters.DateFilter(
        field_name='started_at',
        lookup_expr='gte'
    )
    started_at_before = django_filters.DateFilter(
        field_name='started_at',
        lookup_expr='lte'
    )

    # Filter by WhatsApp session
    whatsapp_session = django_filters.NumberFilter(
        field_name='whatsapp_session_id'
    )

    # Filter by segment
    segment = django_filters.NumberFilter(
        field_name='segment_id'
    )

    class Meta:
        model = Campaign
        fields = [
            'status', 'campaign_type',
            'created_at_after', 'created_at_before',
            'started_at_after', 'started_at_before',
            'whatsapp_session', 'segment'
        ]
