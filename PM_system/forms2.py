from django import forms
from .models import Compressor # Change to the desired model
from django import forms
from crispy_forms.bootstrap import Field, InlineRadios, TabHolder, Tab
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import AppendedText,InlineRadios
from crispy_forms.layout import Layout,Fieldset,Submit,Field,Div,Column,Row,HTML,Button
from datetime import datetime

Comp_var = [("Evap_Entering_Water_Temp" ,"Evap Entering Water Temp (F)"),
             ("Evap_Leaving_Water_Temp","Evap Leaving Water Temp (F)"),
             ("Evap_Saturated_Rfgt_Temp","Evap Saturated Rfgt Temp (F)"),
             ("Evap_Saturated_Rfgt_Pres","Evap Saturated Rfgt Pres (psi)"),
             ("Evap_Rfgt_Approach_Temp","Evap Rfgt Approach Temp (F)"),
             ("Expansion_Valve_Position","Expansion Valve Position (F)"),
             ("Expansion_Valve_Steps","Expansion Valve Steps (mm)"),
             ("Evap_Rfgt_Liquid_Level","Evap Rfgt Liquid Level (%)")

]

Unit = [("0","All"),("1","Trane -1"),("2","Trane -2"),("3","Trane -3")]

class DateForm(forms.Form):
    #start = forms.DateField(widget=forms.DateInput)
    var = forms.CharField(widget = forms.Select(choices=Comp_var), label="Variable")
    unit = forms.CharField(widget = forms.Select(choices=Unit),initial="0")
    start = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required = False)
    end = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),required=False)


    def __init__(self, *args, **kwargs):
        super(DateForm,self).__init__(*args,**kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'  # Not required in Bootstrap 4/5 but can be used
        self.helper.label_class = 'col-md-3 col-form-label'  # Proper label class
        self.helper.field_class = 'col-md-9'
        self.helper.layout = Layout(
            Row(
                Column(Field('var',id = "var_field") ,css_class='form-group col-md-6  '),
                Column('unit', css_class='form-group col-md-6  ', id = "unit_field"),
                css_class = 'form-row'
            ),
            Row(
                Column('start', css_class='form-group col-md-6  ', id = "start_field"),
                Column('end', css_class='form-group col-md-6  ', id = "end_field"),
                css_class = 'form-row'
            ),
            Row(
                Column (HTML("""<div class = "col-md"><button type="submit" class="btn btn-primary w-100"><i class="fa fa-filter" aria-hidden="true"></i> Filter</button></div>"""), css_class = 'form-group col-2'),

                Column(HTML("""<div class = "col-md"><a href = "{% url 'PM_plot' %}" class="btn btn-danger w-100"> <i class="fa fa-eraser" aria-hidden="true"></i> Clear</a></div>"""), css_class = 'form-group col-2'),
                css_class ="row d-flex d-flex justify-content-end"),
        )
