from datetime import timedelta

import django_filters
from django import forms

from .constants import UNIT_NAMES
from .models import Compressor


# Filter choices exclude '0' ("All units"): the filter's empty label
# already covers that case.
CHILLER_UNITS = [
    (key, label)
    for key, label in UNIT_NAMES.items()
    if key != '0'
]


class OrderFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        field_name='date',
        lookup_expr='gte',
        widget=forms.DateInput(attrs={'class': 'form-control filter-control', 'type': 'date'}),
        label='Start Date',
    )
    end_date = django_filters.DateFilter(
        field_name='date',
        method='filter_end_date',
        widget=forms.DateInput(attrs={'class': 'form-control filter-control', 'type': 'date'}),
        label='End Date',
    )
    unit = django_filters.ChoiceFilter(
        field_name='unit',
        lookup_expr='exact',
        choices=CHILLER_UNITS,
        widget=forms.Select(attrs={'class': 'form-select filter-control'}),
        empty_label='Unit Name',
        label='',
    )

    class Meta:
        model = Compressor
        fields = []

    @staticmethod
    def filter_end_date(queryset, name, value):
        if value:
            # Include the whole ending date for the DateTimeField.
            queryset = queryset.filter(date__lt=value + timedelta(days=1))
        return queryset
