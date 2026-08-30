from datetime import datetime, timedelta
from io import BytesIO
import math
from urllib.parse import urlencode

import numpy as np
import plotly.graph_objects as go
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from openpyxl import Workbook

from .filters import OrderFilter
from .forms import CompressorForm
from .forms2 import ControlLimitForm, DateForm
from .models import Compressor, ControlLimit

try:
    import statsmodels.api  # noqa: F401
except ImportError:
    HAS_LOESS = False
else:
    HAS_LOESS = True


def PM_list(request):
    # The template displays compressor.unit for every row.  Fetch the related
    # unit in the same query so a remote Supabase database does not receive
    # one additional query per record.
    context = {
        'compressor_list': Compressor.objects.select_related('unit').order_by('-date', '-pk'),
    }
    return render(request, 'PM_system/compressor_list.html', context)


def PM_filter(request):
    queryset = Compressor.objects.select_related('unit').order_by('-date', '-pk')
    form_filter = OrderFilter(request.GET or None, queryset=queryset)

    sort = request.GET.get('sort')
    sort_fields = {
        'mode': 'Mode',
        '-mode': '-Mode',
        'flow': 'Evap_Flowswitch_Status',
        '-flow': '-Evap_Flowswitch_Status',
    }
    if sort in sort_fields:
        queryset = queryset.order_by(sort_fields[sort], '-pk')
        form_filter = OrderFilter(request.GET or None, queryset=queryset)

    mode_params = request.GET.copy()
    mode_params['sort'] = '-mode' if sort == 'mode' else 'mode'
    flow_params = request.GET.copy()
    flow_params['sort'] = '-flow' if sort == 'flow' else 'flow'

    if 'export' in request.GET:
        return export_excel(form_filter)

    context = {
        'myFilter': form_filter,
        'compressor_list': form_filter.qs,
        'next_mode_sort': '-mode' if sort == 'mode' else 'mode',
        'next_flow_sort': '-flow' if sort == 'flow' else 'flow',
        'mode_sort_url': '?' + urlencode(mode_params, doseq=True),
        'flow_sort_url': '?' + urlencode(flow_params, doseq=True),
    }
    return render(request, 'PM_system/compressor_filter.html', context)


def compressor_form(request, id=0):
    instance = get_object_or_404(Compressor, pk=id) if id else None

    if request.method == 'POST':
        form = CompressorForm(request.POST, instance=instance)
        if form.is_valid():
            compressor = form.save(commit=False)
            selected_date = form.cleaned_data['date']
            current_time = timezone.localtime().time().replace(microsecond=0)
            compressor.date = timezone.make_aware(
                datetime.combine(selected_date, current_time),
                timezone.get_current_timezone(),
            )
            compressor.save()
            return redirect('PM_filter')
    else:
        form = CompressorForm(instance=instance)

    return render(request, 'PM_system/compressor_form.html', {'form': form})


def export_excel(form_filter):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Chiller Data'

    # Keep the export aligned with the recorded-data table and include every
    # field that can be entered on CompressorForm.  The previous list stopped
    # after the first eight columns, which silently dropped newer fields.
    export_columns = [
        ('Unit', 'unit'),
        ('Date', 'date'),
        ('Chill Water Setpoint', 'Chill_Water_Setpoint'),
        ('Current Limit Setpoint', 'Curr_Lim_Setpoint'),
        ('Average Line Current', 'AVg_Line_Curr'),
        ('Mode', 'Mode'),
        ('Evap Flowswitch Status', 'Evap_Flowswitch_Status'),
        ('Evap Entering Water Temp', 'Evap_Entering_Water_Temp'),
        ('Evap Leaving Water Temp', 'Evap_Leaving_Water_Temp'),
        ('Evap Saturated Rfgt Temp', 'Evap_Saturated_Rfgt_Temp'),
        ('Evap Saturated Rfgt Pres', 'Evap_Saturated_Rfgt_Pres'),
        ('Evap Rfgt Approach Temp', 'Evap_Rfgt_Approach_Temp'),
        ('Evap Water PD FT', 'Evap_Water_PD_FT'),
        ('Expansion Valve Position', 'Expansion_Valve_Position'),
        ('Expansion Valve Steps', 'Expansion_Valve_Steps'),
        ('Evap Rfgt Liquid Level', 'Evap_Rfgt_Liquid_Level'),
    ]
    headers = [header for header, _ in export_columns]
    worksheet.append(headers)

    for record in form_filter.qs:
        values = []
        for _, field_name in export_columns:
            value = getattr(record, field_name)
            if field_name == 'unit':
                value = str(value) if value else ''
            elif field_name == 'date' and value and timezone.is_aware(value):
                value = timezone.make_naive(value)
            values.append(value)
        worksheet.append(values)

    buffer = BytesIO()
    workbook.save(buffer)
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="compressor_data.xlsx"'
    return response


def export_view(request):
    queryset = Compressor.objects.all().order_by('-date')
    form_filter = OrderFilter(request.GET or None, queryset=queryset)
    return export_excel(form_filter)


def compressor_delete(request, id):
    if request.method == 'POST':
        compressor = get_object_or_404(Compressor, pk=id)
        compressor.delete()
    return redirect('PM_filter')


def PM_plot(request):
    form2 = DateForm(request.GET or None)
    control_form = ControlLimitForm(request.GET or None)

    default_variable = 'Evap_Entering_Water_Temp'
    variable = default_variable
    unit = '0'

    form_is_valid = form2.is_valid()
    control_form_is_valid = control_form.is_valid()

    cleaned_data = form2.cleaned_data if form_is_valid else {}
    control_data = control_form.cleaned_data if control_form_is_valid else {}

    labels = {
        'Evap_Entering_Water_Temp': 'Evap Entering Water Temp (F)',
        'Evap_Leaving_Water_Temp': 'Evap Leaving Water Temp (F)',
        'Evap_Saturated_Rfgt_Temp': 'Evap Saturated Rfgt Temp (F)',
        'Evap_Saturated_Rfgt_Pres': 'Evap Saturated Rfgt Pres (psi)',
        'Evap_Rfgt_Approach_Temp': 'Evap Rfgt Approach Temp (F)',
        'Expansion_Valve_Position': 'Expansion Valve Position (%)',
        'Expansion_Valve_Steps': 'Expansion Valve Steps (mm)',
        'Evap_Rfgt_Liquid_Level': 'Evap Rfgt Liquid Level (%)',
    }

    measurement_units = {
        'Evap_Entering_Water_Temp': '°F',
        'Evap_Leaving_Water_Temp': '°F',
        'Evap_Saturated_Rfgt_Temp': '°F',
        'Evap_Saturated_Rfgt_Pres': 'psi',
        'Evap_Rfgt_Approach_Temp': '°F',
        'Expansion_Valve_Position': '%',
        'Expansion_Valve_Steps': 'mm',
        'Evap_Rfgt_Liquid_Level': '%',
    }

    requested_variable = cleaned_data.get('var') or request.GET.get('var')
    variable = requested_variable or default_variable
    unit = cleaned_data.get('unit') or request.GET.get('unit') or '0'

    start = cleaned_data.get('start')
    end = cleaned_data.get('end')

    # Default date range: yesterday + today.
    # Only applies when the user has not supplied either date.
    start_param = request.GET.get('start')
    end_param = request.GET.get('end')

    if start is None and end is None and not start_param and not end_param:
        today = timezone.localdate()
        start = today - timedelta(days=1)
        end = today

    if variable not in labels:
        variable = default_variable

    if unit not in {'0', '1', '2', '3'}:
        unit = '0'

    variable_was_selected = requested_variable in labels

    unit_names = {
        '1': 'Trane -1',
        '2': 'Trane -2',
        '3': 'Trane -3',
    }

    # ------------------------------------------------------------------
    # CONTROL LIMITS
    # ------------------------------------------------------------------

    control_limits = ControlLimit.objects.in_bulk(field_name='variable')

    upper_limits = {
        field: control_limits[field].upper_limit
        for field in labels
    }

    lower_limits = {
        field: control_limits[field].lower_limit
        for field in labels
    }

    # ------------------------------------------------------------------
    # BASE DATABASE QUERY
    # ------------------------------------------------------------------

    # Keep records chronologically ordered.
    # Apply unit/date filtering in the database before loading records.
    records_qs = Compressor.objects.all().order_by('date', 'pk')

    if unit != '0':
        records_qs = records_qs.filter(unit_id=unit)

    if start:
        records_qs = records_qs.filter(date__gte=start)

    if end:
        records_qs = records_qs.filter(
            date__lt=end + timedelta(days=1)
        )

    # ------------------------------------------------------------------
    # LATEST ALERT RECORD
    # ------------------------------------------------------------------
    #
    # IMPORTANT:
    # Alerts always use the DATABASE DEFAULT UCL/LCL.
    # Temporary UCL/LCL overrides do NOT affect alerts.
    # ------------------------------------------------------------------

    latest_alert_record = records_qs.filter(
        date__isnull=False
    ).last()

    alert_items = []
    alert_timestamp = None
    alert_unit = None

    if latest_alert_record is not None:
        alert_timestamp = latest_alert_record.date

        alert_unit = unit_names.get(
            str(latest_alert_record.unit_id),
            str(
                latest_alert_record.unit_id
                or 'Unknown unit'
            ),
        )

        for field in sorted(
            labels,
            key=lambda item: labels[item].lower()
        ):
            value = getattr(latest_alert_record, field)

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
                    'label': labels[field],
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

    # Preserve existing automatic alert-based variable selection.
    if not variable_was_selected and alert_items:
        variable = alert_items[0]['field']

    # ------------------------------------------------------------------
    # FORM DEFAULTS
    # ------------------------------------------------------------------

    form2.fields['var'].initial = variable
    form2.fields['unit'].initial = unit
    form2.fields['ucl'].initial = upper_limits[variable]
    form2.fields['lcl'].initial = lower_limits[variable]

    control_form.fields['ucl'].initial = upper_limits[variable]
    control_form.fields['lcl'].initial = lower_limits[variable]

    # ------------------------------------------------------------------
    # TEMPORARY ANALYSIS LIMITS
    # ------------------------------------------------------------------
    #
    # Database limits are the permanent/default limits.
    # Request values are temporary and are never saved.
    # ------------------------------------------------------------------

    upper_limit = float(upper_limits[variable])
    lower_limit = float(lower_limits[variable])

    invalid_limits = False
    limits_overridden = False

    ucl_raw = request.GET.get('ucl')
    lcl_raw = request.GET.get('lcl')

    ucl_supplied = ucl_raw not in (None, '')
    lcl_supplied = lcl_raw not in (None, '')

    if ucl_supplied:
        if control_data.get('ucl') is not None:
            upper_limit = float(control_data['ucl'])
            limits_overridden = True
        else:
            invalid_limits = True

    if lcl_supplied:
        if control_data.get('lcl') is not None:
            lower_limit = float(control_data['lcl'])
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

        upper_limit = float(
            upper_limits[variable]
        )

        lower_limit = float(
            lower_limits[variable]
        )

        limits_overridden = False

    # If invalid limits were supplied, show the actual defaults being used.
    if invalid_limits:
        control_form = ControlLimitForm(
            initial={
                'ucl': upper_limits[variable],
                'lcl': lower_limits[variable],
            }
        )

    # ------------------------------------------------------------------
    # ANALYSIS DATA
    # ------------------------------------------------------------------

    # Filter NULL values in the database first.
    #
    # NaN/infinite values are filtered in Python because database support
    # for those values varies between database engines.
    records_qs = records_qs.filter(
        date__isnull=False,
        **{
            f'{variable}__isnull': False
        },
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
        #
        # They are not:
        # - plotted
        # - counted as anomalies
        # - included in statistics
        if not math.isfinite(value):
            continue

        records.append(record)
        values_list.append(value)
        timestamps.append(record.date)

    values = np.asarray(
        values_list,
        dtype=float,
    )

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

    # ------------------------------------------------------------------
    # STATISTICS DATE RANGE
    # ------------------------------------------------------------------

    def format_date_range(start_date, end_date):
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

    statistics_date_range = format_date_range(
        start,
        end,
    )

    # ------------------------------------------------------------------
    # BASE CONTEXT
    # ------------------------------------------------------------------

    context = {
        'chart': '',
        'form2': form2,
        'control_form': control_form,

        'min': None,
        'max': None,
        'avg': None,
        'std1': None,
        'count': None,

        'var': variable,
        'unit': unit,

        'start': start,
        'end': end,

        # Used by the Summary Statistics section.
        'statistics_date_range': statistics_date_range,

        'variable_label': labels[variable],
        'measurement_unit': measurement_units[variable],

        'percentage': None,

        'ucl': upper_limit,
        'lcl': lower_limit,

        'default_ucl': upper_limits[variable],
        'default_lcl': lower_limits[variable],

        'latest': None,
        'latest_status': None,

        'warning': None,

        'invalid_limits': invalid_limits,

        'alert_items': alert_items,
        'alert_timestamp': alert_timestamp,
        'alert_unit': alert_unit,

        'limits_overridden': (
            limits_overridden
            and not invalid_limits
        ),

        # Built once after statistics are calculated.
        'metric_items': [],
    }

    # ------------------------------------------------------------------
    # NO DATA
    # ------------------------------------------------------------------

    if values.size == 0:
        context['warning'] = (
            'No data available for the selected '
            'variable, unit, and date range.'
        )

        return render(
            request,
            'PM_system/PM_plot.html',
            context,
        )

    # ------------------------------------------------------------------
    # STATISTICS
    # ------------------------------------------------------------------

    minimum = np.min(values)
    maximum = np.max(values)
    average = np.mean(values)

    # Sample standard deviation.
    #
    # A single reading cannot produce a sample standard deviation,
    # so display 0.00 for that case.
    deviation = (
        np.std(values, ddof=1)
        if values.size > 1
        else 0.0
    )

    anomaly_count = int(
        np.count_nonzero(
            (values > upper_limit)
            | (values < lower_limit)
        )
    )

    percentage = (
        anomaly_count / values.size
    ) * 100

    # ------------------------------------------------------------------
    # LATEST VALID PLOTTED READING
    # ------------------------------------------------------------------

    latest = records[-1]
    latest_status = statuses[-1]
    latest_value = float(values[-1])

    latest_timestamp = (
        timezone.localtime(latest.date)
        if timezone.is_aware(latest.date)
        else latest.date
    )

    latest_unit = unit_names.get(
        str(latest.unit_id),
        str(latest.unit_id or '—'),
    )

    warning = (
        latest_status
        if latest_status != 'Within Limits'
        else None
    )

    # ------------------------------------------------------------------
    # PLOT
    # ------------------------------------------------------------------

    figure = go.Figure()

    # Group records by unit.
    #
    # This prevents Plotly from connecting Trane-1 to Trane-2,
    # Trane-2 to Trane-3, etc.
    unit_indexes = {}

    for index, record in enumerate(records):
        unit_key = str(record.unit_id)

        unit_indexes.setdefault(
            unit_key,
            []
        ).append(index)

    # ------------------------------------------------------------------
    # INDIVIDUAL READING LINES
    # ------------------------------------------------------------------

    for unit_key, indexes in unit_indexes.items():

        display_unit = unit_names.get(
            unit_key,
            unit_key or 'Unknown unit',
        )

        unit_customdata = np.column_stack([
            [statuses[i] for i in indexes],
            [upper_limit] * len(indexes),
            [lower_limit] * len(indexes),
            [display_unit] * len(indexes),
        ])

        figure.add_trace(
            go.Scatter(
                x=[
                    timestamps[i]
                    for i in indexes
                ],

                y=[
                    values[i]
                    for i in indexes
                ],

                mode='lines',

                name=display_unit,

                line={
                    'width': 2
                },

                customdata=unit_customdata,

                hovertemplate=(
                    '<b>Individual reading</b><br>'
                    'Timestamp: %{x}<br>'
                    'Value: %{y}<br>'
                    'Unit: %{customdata[3]}<br>'
                    'Status: %{customdata[0]}<br>'
                    'UCL: %{customdata[1]}<br>'
                    'LCL: %{customdata[2]}'
                    '<extra></extra>'
                ),
            )
        )

    # ------------------------------------------------------------------
    # ANOMALY MARKERS
    # ------------------------------------------------------------------

    marker_styles = {
        'Within Limits': (
            'circle',
            '#2563eb',
        ),

        'Above UCL': (
            'triangle-up',
            '#dc2626',
        ),

        'Below LCL': (
            'triangle-down',
            '#d97706',
        ),
    }

    for status, (symbol, color) in marker_styles.items():

        indexes = [
            i
            for i, item in enumerate(statuses)
            if item == status
        ]

        if not indexes:
            continue

        marker_customdata = np.column_stack([
            [upper_limit] * len(indexes),
            [lower_limit] * len(indexes),
            [
                unit_names.get(
                    str(records[i].unit_id),
                    str(
                        records[i].unit_id
                        or '—'
                    ),
                )
                for i in indexes
            ],
        ])

        figure.add_trace(
            go.Scatter(
                x=[
                    timestamps[i]
                    for i in indexes
                ],

                y=[
                    values[i]
                    for i in indexes
                ],

                mode='markers',

                name=status,

                marker={
                    'symbol': symbol,
                    'size': 10,
                    'color': color,
                },

                customdata=marker_customdata,

                hovertemplate=(
                    '<b>Individual reading</b><br>'
                    'Timestamp: %{x}<br>'
                    'Value: %{y}<br>'
                    'Unit: %{customdata[2]}<br>'
                    f'Status: {status}<br>'
                    'UCL: %{customdata[0]}<br>'
                    'LCL: %{customdata[1]}'
                    '<extra></extra>'
                ),
            )
        )

    # ------------------------------------------------------------------
    # CONTROL LIMIT LINES
    # ------------------------------------------------------------------

    figure.add_hline(
        y=upper_limit,
        line_dash='dash',
        line_color='#dc2626',
        annotation_text=(
            f'UCL ({upper_limit:g})'
        ),
        annotation_position='top right',
    )

    figure.add_hline(
        y=lower_limit,
        line_dash='dash',
        line_color='#d97706',
        annotation_text=(
            f'LCL ({lower_limit:g})'
        ),
        annotation_position='bottom right',
    )

    # ------------------------------------------------------------------
    # CHART LAYOUT
    # ------------------------------------------------------------------

    figure.update_layout(
        title={
            'text': labels[variable],
            'font_size': 22,
            'xanchor': 'center',
            'x': 0.5,
        },

        xaxis_title='Date / time',

        yaxis_title=labels[variable],

        template='plotly_white',

        hovermode='closest',

        legend={
            'orientation': 'h',
            'y': -0.2,
        },

        margin={
            't': 70,
            'b': 90,
        },
    )

    metric_items = [
        (
            'Mean',
            round(float(average), 2)
        ),

        (
            'Maximum',
            round(float(maximum), 2)
        ),

        (
            'Minimum',
            round(float(minimum), 2)
        ),

        (
            'Standard deviation',
            round(float(deviation), 2)
        ),

        (
            'Anomaly count',
            anomaly_count
        ),

        (
            'Anomaly percentage',
            f'{percentage:.2f}%'
        ),
    ]

    # ------------------------------------------------------------------
    # FINAL CONTEXT
    # ------------------------------------------------------------------

    context.update({
        'chart': figure.to_html(
            full_html=False,
            include_plotlyjs='cdn',
            config={
                'responsive': True,
            },
        ),

        'min': round(
            float(minimum),
            2,
        ),

        'max': round(
            float(maximum),
            2,
        ),

        'avg': round(
            float(average),
            2,
        ),

        'std1': round(
            float(deviation),
            2,
        ),

        'count': anomaly_count,

        'percentage': round(
            float(percentage),
            2,
        ),

        'latest': {
            'timestamp': latest_timestamp,
            'value': round(
                latest_value,
                2,
            ),
            'unit': latest_unit,
        },

        'latest_status': latest_status,

        'warning': warning,

        'limits_overridden': (
            limits_overridden
            and not invalid_limits
        ),

        'variable_label': labels[variable],

        'measurement_unit': measurement_units[variable],

        'metric_items': metric_items,
    })

    return render(
        request,
        'PM_system/PM_plot.html',
        context,
    )


def Home(request):
    return render(request, 'PM_system/Home.html')


def root_redirect(request):
    return redirect('home')
