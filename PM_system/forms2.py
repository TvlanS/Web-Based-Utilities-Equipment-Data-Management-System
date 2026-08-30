from crispy_forms.bootstrap import Field
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, HTML, Layout, Row
from django import forms

from .constants import UNIT_NAMES, VARIABLE_LABELS

# Choice lists are derived from constants.py so the dropdowns can never
# drift out of sync with the plot, statistics, or filter.
Comp_var = list(VARIABLE_LABELS.items())
Unit = list(UNIT_NAMES.items())


class DateForm(forms.Form):
    var = forms.CharField(widget=forms.Select(choices=Comp_var, attrs={'class': 'pm-select'}), label="Variable")
    unit = forms.CharField(widget=forms.Select(choices=Unit, attrs={'class': 'pm-select'}), initial="0")
    start = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'pm-input'}), required=False)
    end = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'pm-input'}), required=False)
    ucl = forms.FloatField(label='UCL', required=False, widget=forms.NumberInput(attrs={'class': 'pm-input', 'step': 'any'}))
    lcl = forms.FloatField(label='LCL', required=False, widget=forms.NumberInput(attrs={'class': 'pm-input', 'step': 'any'}))

    def __init__(self, *args, **kwargs):
        super(DateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'  # Not required in Bootstrap 4/5 but can be used
        self.helper.label_class = 'col-md-3 col-form-label'  # Proper label class
        self.helper.field_class = 'col-md-9'
        self.helper.layout = Layout(
            Row(
                Column(Field('var', id="var_field"), css_class='form-group col-md-6  '),
                Column('unit', css_class='form-group col-md-6  ', id="unit_field"),
                css_class='form-row'
            ),
            Row(
                Column('start', css_class='form-group col-md-6  ', id="start_field"),
                Column('end', css_class='form-group col-md-6  ', id="end_field"),
                css_class='form-row'
            ),
            Row(
                Column('ucl', css_class='form-group col-md-6', id='ucl_field'),
                Column('lcl', css_class='form-group col-md-6', id='lcl_field'),
                css_class='form-row'
            ),
            Row(
                Column(HTML("""<div class = "col-md"><button type="submit" class="btn btn-primary w-100"><i class="fa fa-filter" aria-hidden="true"></i> Filter</button></div>"""), css_class='form-group col-2'),

                Column(HTML("""<div class = "col-md"><a href = "{% url 'PM_plot' %}" class="btn btn-danger w-100"> <i class="fa fa-eraser" aria-hidden="true"></i> Clear</a></div>"""), css_class='form-group col-2'),
                css_class="row d-flex d-flex justify-content-end"),
        )


class ControlLimitForm(forms.Form):
    ucl = forms.FloatField(label='UCL', required=False, widget=forms.NumberInput(attrs={'class': 'pm-input', 'step': 'any'}))
    lcl = forms.FloatField(label='LCL', required=False, widget=forms.NumberInput(attrs={'class': 'pm-input', 'step': 'any'}))
