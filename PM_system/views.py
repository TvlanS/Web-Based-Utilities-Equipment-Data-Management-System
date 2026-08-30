from datetime import datetime, timedelta
from io import BytesIO
from urllib.parse import urlencode

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from openpyxl import Workbook

from .charts import build_time_series_figure
from .constants import MEASUREMENT_UNITS, UNIT_NAMES, VARIABLE_LABELS
from .filters import OrderFilter
from .forms import CompressorForm
from .forms2 import ControlLimitForm, DateForm
from .models import Compressor
from .services import (
    build_alerts,
    compute_statistics,
    format_date_range,
    load_control_limits,
    load_series,
    resolve_limits,
)


def compressor_list(request):
    # The template displays compressor.unit for every row.  Fetch the related
    # unit in the same query so a remote Supabase database does not receive
    # one additional query per record.
    context = {
        'compressor_list': Compressor.objects.select_related('unit').order_by('-date', '-pk'),
    }
    return render(request, 'PM_system/compressor_list.html', context)


def compressor_filter(request):
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


def compressor_export(request):
    queryset = Compressor.objects.all().order_by('-date')
    form_filter = OrderFilter(request.GET or None, queryset=queryset)
    return export_excel(form_filter)


def compressor_delete(request, id):
    if request.method == 'POST':
        compressor = get_object_or_404(Compressor, pk=id)
        compressor.delete()
    return redirect('PM_filter')


def compressor_plot(request):
    form2 = DateForm(request.GET or None)
    control_form = ControlLimitForm(request.GET or None)

    default_variable = 'Evap_Entering_Water_Temp'
    variable = default_variable
    unit = '0'

    form_is_valid = form2.is_valid()
    control_form_is_valid = control_form.is_valid()

    cleaned_data = form2.cleaned_data if form_is_valid else {}
    control_data = control_form.cleaned_data if control_form_is_valid else {}

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

    if variable not in VARIABLE_LABELS:
        variable = default_variable

    if unit not in {'0', '1', '2', '3'}:
        unit = '0'

    variable_was_selected = requested_variable in VARIABLE_LABELS

    # ------------------------------------------------------------------
    # CONTROL LIMITS
    # ------------------------------------------------------------------

    upper_limits, lower_limits = load_control_limits(VARIABLE_LABELS)

    # ------------------------------------------------------------------
    # LATEST ALERT RECORD
    # ------------------------------------------------------------------
    #
    # Alerts always use the DATABASE DEFAULT UCL/LCL.
    # Temporary UCL/LCL overrides do NOT affect alerts.
    # ------------------------------------------------------------------

    alert_items, alert_timestamp, alert_unit = build_alerts(
        unit, start, end, upper_limits, lower_limits, VARIABLE_LABELS,
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

    upper_limit, lower_limit, limits_overridden, invalid_limits = resolve_limits(
        upper_limits,
        lower_limits,
        variable,
        request.GET.get('ucl'),
        request.GET.get('lcl'),
        control_data,
    )

    # If invalid limits were supplied, show the actual defaults being used.
    if invalid_limits:
        control_form = ControlLimitForm(
            initial={
                'ucl': upper_limits[variable],
                'lcl': lower_limits[variable],
            }
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
        'statistics_date_range': format_date_range(start, end),

        'variable_label': VARIABLE_LABELS[variable],
        'measurement_unit': MEASUREMENT_UNITS[variable],

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
    # ANALYSIS DATA
    # ------------------------------------------------------------------

    records, values, timestamps, statuses = load_series(
        variable, unit, start, end, upper_limit, lower_limit,
    )

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

    stats = compute_statistics(values, upper_limit, lower_limit)

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

    latest_unit = UNIT_NAMES.get(
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

    figure = build_time_series_figure(
        records,
        values,
        timestamps,
        statuses,
        VARIABLE_LABELS[variable],
        upper_limit,
        lower_limit,
    )

    metric_items = [
        ('Mean', round(float(stats['avg']), 2)),
        ('Maximum', round(float(stats['max']), 2)),
        ('Minimum', round(float(stats['min']), 2)),
        ('Standard deviation', round(float(stats['std']), 2)),
        ('Anomaly count', stats['anomaly_count']),
        ('Anomaly percentage', f'{stats["anomaly_percentage"]:.2f}%'),
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

        'min': round(float(stats['min']), 2),
        'max': round(float(stats['max']), 2),
        'avg': round(float(stats['avg']), 2),
        'std1': round(float(stats['std']), 2),
        'count': stats['anomaly_count'],
        'percentage': round(float(stats['anomaly_percentage']), 2),

        'latest': {
            'timestamp': latest_timestamp,
            'value': round(latest_value, 2),
            'unit': latest_unit,
        },

        'latest_status': latest_status,
        'warning': warning,
        'limits_overridden': (
            limits_overridden
            and not invalid_limits
        ),
        'variable_label': VARIABLE_LABELS[variable],
        'measurement_unit': MEASUREMENT_UNITS[variable],
        'metric_items': metric_items,
    })

    return render(
        request,
        'PM_system/PM_plot.html',
        context,
    )


def home(request):
    return render(request, 'PM_system/Home.html')


def root_redirect(request):
    return redirect('home')
