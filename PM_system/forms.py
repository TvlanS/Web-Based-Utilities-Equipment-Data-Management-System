from crispy_forms.bootstrap import AppendedText, InlineRadios
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, HTML, Layout, Row
from django import forms
from django.utils import timezone

from .models import Compressor


class CompressorForm(forms.ModelForm):
    FLOW_CHOICES = [
        ('Flow', 'Flow'),
        ('No flow', 'No Flow'),
    ]
    MODE_CHOICES = [
        ('Run', 'Run'),
        ('Offline', 'Offline'),
        ('Cooling', 'Cooling'),
        ('Standby', 'Standby'),
    ]

    Evap_Flowswitch_Status = forms.ChoiceField(
        choices=FLOW_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-inline'}),
    )
    Mode = forms.ChoiceField(
        choices=MODE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-inline'}),
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=timezone.localdate,
    )

    class Meta:
        model = Compressor
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].empty_label = 'Select'

        # Keep form validation aligned with nullable measurement columns.
        required_fields = {'date', 'unit', 'Mode', 'Evap_Flowswitch_Status'}
        for field_name, field in self.fields.items():
            field.required = field_name in required_fields

        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-6 col-form-label'
        self.helper.field_class = 'col-md-6'
        self.helper.layout = Layout(
            Row(
                Column('date', css_class='form-group col-md-6'),
                Column('unit', css_class='form-group col-md-6'),
                css_class='form-row',
            ),
            HTML('<hr><div class="display-6">Main Tab</div>'),
            Row(
                Column(InlineRadios('Mode'), css_class='form-group col-md-6'),
                Column(AppendedText('Chill_Water_Setpoint', 'F'), css_class='form-group col-md-6'),
            ),
            Row(
                Column(AppendedText('AVg_Line_Curr', '% RLA'), css_class='form-group col-md-6'),
                Column(AppendedText('Curr_Lim_Setpoint', '% RLA'), css_class='form-group col-md-6'),
            ),
            HTML('<hr><div class="display-6">Evaporator</div>'),
            Row(
                Column(AppendedText('Evap_Entering_Water_Temp', '°C'), css_class='form-group col-6'),
                Column(AppendedText('Evap_Leaving_Water_Temp', '°C'), css_class='form-group col-6'),
            ),
            Row(
                Column(AppendedText('Evap_Saturated_Rfgt_Temp', '°C'), css_class='form-group col-6'),
                Column(AppendedText('Evap_Saturated_Rfgt_Pres', 'Pa'), css_class='form-group col-6'),
            ),
            Row(
                Column(InlineRadios('Evap_Flowswitch_Status'), css_class='form-group col-6'),
                Column(AppendedText('Evap_Rfgt_Approach_Temp', '°C'), css_class='form-group col-6'),
            ),
            Row(
                Column(AppendedText('Expansion_Valve_Position', '%'), css_class='form-group col-6'),
                Column(AppendedText('Expansion_Valve_Steps', ''), css_class='form-group col-6'),
            ),
            Row(
                Column(AppendedText('Evap_Rfgt_Liquid_Level', 'mm'), css_class='form-group col-6'),
            ),
            Row(
                Column(
                    HTML('<button type="submit" class="btn btn-success w-100"><i class="fa fa-id-card-o"></i> Submit</button>'),
                    css_class='form-group col-6',
                ),
                Column(
                    HTML('<a href="{% url \'PM_filter\' %}" class="btn btn-secondary w-100"><i class="fas fa-stream"></i> Back to list</a>'),
                    css_class='form-group col-6',
                ),
            ),
        )
