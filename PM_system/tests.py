import math
from datetime import date

import numpy as np
from django.test import TestCase
from django.utils import timezone

from .constants import VARIABLE_LABELS
from .models import Compressor, CompressorUnit, ControlLimit
from .services import (
    build_alerts,
    compute_statistics,
    format_date_range,
    load_control_limits,
    resolve_limits,
)


class ComputeStatisticsTests(TestCase):
    def test_basic_statistics(self):
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        stats = compute_statistics(values, upper_limit=4.5, lower_limit=1.5)

        self.assertEqual(stats['min'], 1.0)
        self.assertEqual(stats['max'], 5.0)
        self.assertEqual(stats['avg'], 3.0)
        self.assertAlmostEqual(stats['std'], np.std(values, ddof=1))
        # Above UCL: 5.0. Below LCL: 1.0.
        self.assertEqual(stats['anomaly_count'], 2)
        self.assertAlmostEqual(stats['anomaly_percentage'], 40.0)

    def test_single_reading_stddev_is_zero(self):
        values = np.array([7.0])
        stats = compute_statistics(values, upper_limit=10, lower_limit=0)

        self.assertEqual(stats['std'], 0.0)
        self.assertEqual(stats['anomaly_count'], 0)
        self.assertAlmostEqual(stats['anomaly_percentage'], 0.0)

    def test_no_anomalies(self):
        values = np.array([2.0, 3.0, 4.0])
        stats = compute_statistics(values, upper_limit=10, lower_limit=1)

        self.assertEqual(stats['anomaly_count'], 0)
        self.assertAlmostEqual(stats['anomaly_percentage'], 0.0)


class ResolveLimitsTests(TestCase):
    def setUp(self):
        self.variable = 'Evap_Entering_Water_Temp'
        self.upper = {field: 15.0 for field in VARIABLE_LABELS}
        self.lower = {field: 5.0 for field in VARIABLE_LABELS}

    def test_defaults_when_nothing_supplied(self):
        upper, lower, overridden, invalid = resolve_limits(
            self.upper, self.lower, self.variable, None, None, {}
        )
        self.assertEqual((upper, lower), (15.0, 5.0))
        self.assertFalse(overridden)
        self.assertFalse(invalid)

    def test_valid_override_is_temporary(self):
        upper, lower, overridden, invalid = resolve_limits(
            self.upper, self.lower, self.variable,
            '20', '0', {'ucl': 20.0, 'lcl': 0.0},
        )
        self.assertEqual((upper, lower), (20.0, 0.0))
        self.assertTrue(overridden)
        self.assertFalse(invalid)

    def test_reversed_limits_fall_back_to_defaults(self):
        upper, lower, overridden, invalid = resolve_limits(
            self.upper, self.lower, self.variable,
            '2', '10', {'ucl': 2.0, 'lcl': 10.0},
        )
        self.assertEqual((upper, lower), (15.0, 5.0))
        self.assertFalse(overridden)
        self.assertTrue(invalid)

    def test_unparseable_ucl_marks_invalid_but_keeps_defaults(self):
        upper, lower, overridden, invalid = resolve_limits(
            self.upper, self.lower, self.variable, 'abc', None, {}
        )
        self.assertEqual((upper, lower), (15.0, 5.0))
        self.assertFalse(overridden)
        self.assertTrue(invalid)


class LoadControlLimitsTests(TestCase):
    def test_missing_control_limit_degrades_to_no_constraint(self):
        # The 0008 data migration seeds every variable, so delete one row
        # to exercise the missing-row fallback.
        ControlLimit.objects.filter(variable='Evap_Leaving_Water_Temp').delete()

        upper, lower = load_control_limits(VARIABLE_LABELS)

        self.assertEqual(upper['Evap_Entering_Water_Temp'], 15.0)
        self.assertEqual(lower['Evap_Entering_Water_Temp'], 5.0)

        # A variable without a ControlLimit row must not crash the page.
        self.assertEqual(upper['Evap_Leaving_Water_Temp'], math.inf)
        self.assertEqual(lower['Evap_Leaving_Water_Temp'], -math.inf)


class BuildAlertsTests(TestCase):
    def setUp(self):
        # Unit ids are the conventional '1'/'2'/'3' used across the app.
        self.unit = CompressorUnit.objects.create(id=1, Unit='Trane -1')
        self.upper = {field: 15.0 for field in VARIABLE_LABELS}
        self.lower = {field: 5.0 for field in VARIABLE_LABELS}

    def test_no_records_returns_empty(self):
        items, timestamp, unit = build_alerts(
            '1', None, None, self.upper, self.lower, VARIABLE_LABELS
        )
        self.assertEqual(items, [])
        self.assertIsNone(timestamp)
        self.assertIsNone(unit)

    def test_out_of_limit_value_flags_alert(self):
        Compressor.objects.create(
            unit=self.unit,
            date=timezone.now(),
            Evap_Entering_Water_Temp=30,
            Mode='Run',
            Evap_Flowswitch_Status='Flow',
        )
        items, timestamp, unit = build_alerts(
            '1', None, None, self.upper, self.lower, VARIABLE_LABELS
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['field'], 'Evap_Entering_Water_Temp')
        self.assertEqual(items[0]['status'], 'Above UCL')
        self.assertEqual(unit, 'Trane -1')
        self.assertIsNotNone(timestamp)

    def test_below_lcl_sorted_before_above_ucl(self):
        Compressor.objects.create(
            unit=self.unit,
            date=timezone.now(),
            Evap_Entering_Water_Temp=30,  # above UCL
            Evap_Leaving_Water_Temp=1,    # below LCL
            Mode='Run',
            Evap_Flowswitch_Status='Flow',
        )
        items, _, _ = build_alerts(
            '1', None, None, self.upper, self.lower, VARIABLE_LABELS
        )
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['field'], 'Evap_Leaving_Water_Temp')
        self.assertEqual(items[0]['status'], 'Below LCL')
        self.assertEqual(items[1]['field'], 'Evap_Entering_Water_Temp')
        self.assertEqual(items[1]['status'], 'Above UCL')


class FormatDateRangeTests(TestCase):
    def test_full_range(self):
        self.assertEqual(
            format_date_range(date(2026, 1, 1), date(2026, 1, 5)),
            'Jan 1, 2026 – Jan 5, 2026',
        )

    def test_open_ended_ranges(self):
        self.assertEqual(
            format_date_range(date(2026, 1, 1), None),
            'From Jan 1, 2026',
        )
        self.assertEqual(
            format_date_range(None, date(2026, 1, 5)),
            'Through Jan 5, 2026',
        )
        self.assertEqual(
            format_date_range(None, None),
            'All available dates',
        )
