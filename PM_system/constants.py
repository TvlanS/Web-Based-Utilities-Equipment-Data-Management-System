"""Single source of truth for variable and unit metadata.

Every label, measurement unit, and chiller unit name used across the
forms, filters, views, services, and charts must come from here so the
lists can never drift out of sync again (previously they lived in three
places and had already disagreed: Expansion_Valve_Position was shown as
both "(F)" and "(%)", and Trane units as both "Trane-1" and "Trane -1").
"""

# Display labels for every plotted Compressor field.
VARIABLE_LABELS = {
    'Evap_Entering_Water_Temp': 'Evap Entering Water Temp (F)',
    'Evap_Leaving_Water_Temp': 'Evap Leaving Water Temp (F)',
    'Evap_Saturated_Rfgt_Temp': 'Evap Saturated Rfgt Temp (F)',
    'Evap_Saturated_Rfgt_Pres': 'Evap Saturated Rfgt Pres (psi)',
    'Evap_Rfgt_Approach_Temp': 'Evap Rfgt Approach Temp (F)',
    'Expansion_Valve_Position': 'Expansion Valve Position (%)',
    'Expansion_Valve_Steps': 'Expansion Valve Steps (mm)',
    'Evap_Rfgt_Liquid_Level': 'Evap Rfgt Liquid Level (%)',
}

# Measurement unit shown next to statistic values.
MEASUREMENT_UNITS = {
    'Evap_Entering_Water_Temp': '°F',
    'Evap_Leaving_Water_Temp': '°F',
    'Evap_Saturated_Rfgt_Temp': '°F',
    'Evap_Saturated_Rfgt_Pres': 'psi',
    'Evap_Rfgt_Approach_Temp': '°F',
    'Expansion_Valve_Position': '%',
    'Expansion_Valve_Steps': 'mm',
    'Evap_Rfgt_Liquid_Level': '%',
}

# Chiller units: database id -> display name. '0' means "All units".
UNIT_NAMES = {
    '0': 'All',
    '1': 'Trane -1',
    '2': 'Trane -2',
    '3': 'Trane -3',
}
