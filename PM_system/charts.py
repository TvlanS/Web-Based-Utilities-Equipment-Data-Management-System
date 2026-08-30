"""Plotly chart builders for chiller analytics.

These functions only build figures; they never touch the database or the
request. Views hand them already-loaded, already-cleaned data and receive
a ready-to-render ``go.Figure`` back.
"""

import numpy as np
import plotly.graph_objects as go

from .constants import UNIT_NAMES


def build_time_series_figure(records, values, timestamps, statuses, variable_label, upper_limit, lower_limit):
    """Build the individual-readings chart with anomaly markers and limits."""
    figure = go.Figure()

    # Group records by unit.
    #
    # This prevents Plotly from connecting Trane-1 to Trane-2,
    # Trane-2 to Trane-3, etc.
    unit_indexes = {}

    for index, record in enumerate(records):
        unit_key = str(record.unit_id)
        unit_indexes.setdefault(unit_key, []).append(index)

    # ------------------------------------------------------------------
    # INDIVIDUAL READING LINES
    # ------------------------------------------------------------------

    for unit_key, indexes in unit_indexes.items():
        display_unit = UNIT_NAMES.get(
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
                x=[timestamps[i] for i in indexes],
                y=[values[i] for i in indexes],
                mode='lines',
                name=display_unit,
                line={'width': 2},
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
        'Within Limits': ('circle', '#2563eb'),
        'Above UCL': ('triangle-up', '#dc2626'),
        'Below LCL': ('triangle-down', '#d97706'),
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
                UNIT_NAMES.get(
                    str(records[i].unit_id),
                    str(records[i].unit_id or '—'),
                )
                for i in indexes
            ],
        ])

        figure.add_trace(
            go.Scatter(
                x=[timestamps[i] for i in indexes],
                y=[values[i] for i in indexes],
                mode='markers',
                name=status,
                marker={'symbol': symbol, 'size': 10, 'color': color},
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
        annotation_text=f'UCL ({upper_limit:g})',
        annotation_position='top right',
    )

    figure.add_hline(
        y=lower_limit,
        line_dash='dash',
        line_color='#d97706',
        annotation_text=f'LCL ({lower_limit:g})',
        annotation_position='bottom right',
    )

    # ------------------------------------------------------------------
    # CHART LAYOUT
    # ------------------------------------------------------------------

    figure.update_layout(
        title={
            'text': variable_label,
            'font_size': 22,
            'xanchor': 'center',
            'x': 0.5,
        },
        xaxis_title='Date / time',
        yaxis_title=variable_label,
        template='plotly_white',
        hovermode='closest',
        legend={'orientation': 'h', 'y': -0.2},
        margin={'t': 70, 'b': 90},
    )

    return figure
