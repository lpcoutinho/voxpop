"""
Filters for Supporters API.
"""
import django_filters
from django.db.models import Q

from apps.supporters.models import Supporter, Tag


class SupporterFilter(django_filters.FilterSet):
    """Filter for Supporter list endpoint."""

    # Text filters
    city = django_filters.CharFilter(lookup_expr='icontains')
    state = django_filters.CharFilter(lookup_expr='iexact')
    neighborhood = django_filters.CharFilter(lookup_expr='icontains')
    gender = django_filters.CharFilter(lookup_expr='iexact')
    electoral_zone = django_filters.CharFilter(lookup_expr='iexact')
    source = django_filters.CharFilter(lookup_expr='iexact')

    # Boolean filter
    whatsapp_opt_in = django_filters.BooleanFilter()

    # Tags filter (supports multiple)
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__id',
        to_field_name='id',
        queryset=Tag.objects.filter(is_active=True),
        conjoined=False  # OR logic (any tag)
    )

    # Tags filter with AND logic (all tags required)
    tags_all = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__id',
        to_field_name='id',
        queryset=Tag.objects.filter(is_active=True),
        conjoined=True  # AND logic (all tags)
    )

    # Date range filters
    created_at_after = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_at_before = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte'
    )

    # Age range filters (calculated from birth_date)
    age_min = django_filters.NumberFilter(method='filter_age_min')
    age_max = django_filters.NumberFilter(method='filter_age_max')

    # General search
    search = django_filters.CharFilter(method='filter_search')

    # Contact status filter (lead, apoiador, blacklist)
    contact_status = django_filters.CharFilter(method='filter_contact_status')

    class Meta:
        model = Supporter
        fields = [
            'city', 'state', 'neighborhood', 'gender',
            'electoral_zone', 'source', 'whatsapp_opt_in',
            'tags', 'tags_all',
            'created_at_after', 'created_at_before',
            'age_min', 'age_max', 'search', 'contact_status'
        ]

    def filter_search(self, queryset, name, value):
        """
        Search across multiple fields.
        """
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(phone__icontains=value) |
            Q(email__icontains=value) |
            Q(city__icontains=value)
        )

    def filter_age_min(self, queryset, name, value):
        """
        Filter supporters with age >= value.
        """
        if value is None:
            return queryset

        from datetime import date
        from dateutil.relativedelta import relativedelta

        max_birth_date = date.today() - relativedelta(years=value)
        return queryset.filter(birth_date__lte=max_birth_date)

    def filter_age_max(self, queryset, name, value):
        """
        Filter supporters with age <= value.
        """
        if value is None:
            return queryset

        from datetime import date
        from dateutil.relativedelta import relativedelta

        min_birth_date = date.today() - relativedelta(years=value + 1) + relativedelta(days=1)
        return queryset.filter(birth_date__gte=min_birth_date)

    def filter_contact_status(self, queryset, name, value):
        """
        Filter supporters by contact status (based on system tags).
        Accepts: 'lead', 'apoiador', 'blacklist'
        """
        if not value:
            return queryset

        value = value.lower()

        if value == 'lead':
            return queryset.filter(tags__slug='lead', tags__is_system=True)
        elif value == 'apoiador':
            return queryset.filter(tags__slug='apoiador', tags__is_system=True)
        elif value == 'blacklist':
            return queryset.filter(tags__slug='blacklist', tags__is_system=True)

        return queryset
