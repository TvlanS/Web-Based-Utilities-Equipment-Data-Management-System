"""Domain logic for chiller analytics.

Everything here is a plain function: no request, no render, no HTTP.
Views orchestrate these functions, and charts.py turns the returned
data into a Plotly figure.
"""

import math
from datetime import timedelta

import numpy as np

from .constants import UNIT_NAMES
from .models import Compressor, ControlLimit


def load_control_limits(variable_labels):
    """Load the database-backed default UCL/LCL for each plotted variable.

    A missing ControlLimit row degrades to an unbounded limit ("no
    constraint") instead of crashing the page with a KeyError.
    """
    limits = ControlLimit.objects.in_bulk(field_name='variable')

    upper_limits = {
        field: limits[field].upper_limit if field in limits else math.inf
        for field in variable_labels
    }
    lower_limits = {
        field: limits[field].lower_limit if field in limits else -math.inf
        for field in variable_labels
    }
    return upper_limits, lower_limits


def _filtered_records(unit, start, end):
    """Compressor records ordered chronologically, scoped by unit/date."""
    records_qs = Compressor.objects.all().order_by('date', 'pk')

    if unit != '0':
        records_qs = records_qs.filter(unit_id=unit)

    if start:
        records_qs = records_qs.filter(date__gte=start)

    if end:
        records_qs = records_qs.filter(date__lt=end + timedelta(days=1))

    return records_qs


def load_series(variable, unit, start, end, upper_limit, lower_limit):
    """Load and clean the requested variable's readings.

    Returns ``(records, values, timestamps, statuses)`` where ``values``
    is a numpy array of finite floats. NULL, NaN, and infinite rows are
    dropped entirely: they are not plotted, not counted as anomalies, and
    not included in the statistics.
    """
    records_qs = _filtered_records(unit, start, end)

    records_qs = records_qs.filter(
        date__isnull=False,
        **{f'{variable}__isnull': False},
    )

    records = []
    values_list = []
    timestamps = []

    for record in records_qs:
        raw_value = getattr(record, variable)

        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue

        # Skip NaN and infinite values completely.
        if not math.isfinite(value):
            continue

        records.append(record)
        values_list.append(value)
        timestamps.append(record.date)

    values = np.asarray(values_list, dtype=float)

    statuses = [
        (
            'Above UCL'
            if value > upper_limit
            else 'Below LCL'
            if value < lower_limit
            else 'Within Limits'
        )
        for value in values
    ]

    return records, values, timestamps, statuses


def compute_statistics(values, upper_limit, lower_limit):
    """Return summary statistics for a series of readings.

    ``values`` must be a non-empty numpy array of finite floats.
    """
    minimum = np.min(values)
    maximum = np.max(values)
    average = np.mean(values)

    # Sample standard deviation.
    #
    # A single reading cannot produce a sample standard deviation,
    # so return 0.0 for that case.
    deviation = np.std(values, ddof=1) if values.size > 1 else 0.0

    anomaly_count = int(
        np.count_nonzero(
            (values > upper_limit)
            | (values < lower_limit)
        )
    )

    percentage = (anomaly_count / values.size) * 100

    return {
        'min': minimum,
        'max': maximum,
        'avg': average,
        'std': deviation,
        'anomaly_count': anomaly_count,
        'anomaly_percentage': percentage,
    }


def build_alerts(unit, start, end, upper_limits, lower_limits, variable_labels):
    """Return alert items for the latest record within the date range.

    Returns ``(alert_items, alert_timestamp, alert_unit)``.

    Alerts always use the DATABASE DEFAULT UCL/LCL. Temporary UCL/LCL
    overrides do NOT affect alerts.
    """
    latest = _filtered_records(unit, start, end).filter(date__isnull=False).last()

    if latest is None:
        return [], None, None

    alert_timestamp = latest.date

    alert_unit = UNIT_NAMES.get(
        str(latest.unit_id),
        str(latest.unit_id or 'Unknown unit'),
    )

    alert_items = []

    for field in sorted(
        variable_labels,
        key=lambda item: variable_labels[item].lower()
    ):
        value = getattr(latest, field)

        if value is None:
            continue

        try:
            value = float(value)
        except (TypeError, ValueError):
            continue

        # Ignore NaN / infinite values.
        if not math.isfinite(value):
            continue

        default_ucl = float(upper_limits[field])
        default_lcl = float(lower_limits[field])

        status = (
            'Above UCL'
            if value > default_ucl
            else 'Below LCL'
            if value < default_lcl
            else None
        )

        if status:
            alert_items.append({
                'field': field,
                'label': variable_labels[field],
                'value': value,
                'status': status,
                'ucl': default_ucl,
                'lcl': default_lcl,
            })

    alert_items.sort(
        key=lambda item: (
            0 if item['status'] == 'Below LCL' else 1,
            item['label'].lower(),
        )
    )

    return alert_items, alert_timestamp, alert_unit


def resolve_limits(upper_limits, lower_limits, variable, ucl_raw, lcl_raw, cleaned_limits):
    """Resolve the effective UCL/LCL for the plotted variable.

    Database limits are the permanent defaults. Request values are
    temporary and are never saved.

    Returns ``(upper_limit, lower_limit, limits_overridden, invalid_limits)``.
    """
    upper_limit = float(upper_limits[variable])
    lower_limit = float(lower_limits[variable])

    invalid_limits = False
    limits_overridden = False

    ucl_supplied = ucl_raw not in (None, '')
    lcl_supplied = lcl_raw not in (None, '')

    if ucl_supplied:
        if cleaned_limits.get('ucl') is not None:
            upper_limit = float(cleaned_limits['ucl'])
            limits_overridden = True
        else:
            invalid_limits = True

    if lcl_supplied:
        if cleaned_limits.get('lcl') is not None:
            lower_limit = float(cleaned_limits['lcl'])
            limits_overridden = True
        else:
            invalid_limits = True

    # UCL must be strictly greater than LCL.
    if (
        not math.isfinite(upper_limit)
        or not math.isfinite(lower_limit)
        or upper_limit <= lower_limit
    ):
        invalid_limits = True

        upper_limit = float(upper_limits[variable])
        lower_limit = float(lower_limits[variable])

        limits_overridden = False

    return upper_limit, lower_limit, limits_overridden, invalid_limits


def format_date_range(start_date, end_date):
    """Human-readable description of the statistics date range."""
    if start_date and end_date:
        return (
            f'{start_date.strftime("%b")} '
            f'{start_date.day}, '
            f'{start_date.year} '
            f'– '
            f'{end_date.strftime("%b")} '
            f'{end_date.day}, '
            f'{end_date.year}'
        )

    if start_date:
        return (
            f'From {start_date.strftime("%b")} '
            f'{start_date.day}, '
            f'{start_date.year}'
        )

    if end_date:
        return (
            f'Through {end_date.strftime("%b")} '
            f'{end_date.day}, '
            f'{end_date.year}'
        )

    return 'All available dates'
