import django_filters
from .models import Compressor
from datetime import date
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import AppendedText,InlineRadios
from crispy_forms.layout import Layout,Fieldset,Submit,Field,Div,Column,Row,HTML,Button

ChillerUnit = [
('1', 'Trane-1'),
('2', 'Trane-2'),
('3', 'Trane-3'),
]



class OrderFilter(django_filters.FilterSet):
    
    date_range = django_filters.DateFromToRangeFilter(
        field_name='date',
        lookup_expr='date__range',
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'}),
        initial=date.today(),
        label=''    ) 

    unit = django_filters.ChoiceFilter(
        field_name='unit',
        lookup_expr='exact',
        choices=ChillerUnit,
        empty_label='Select' ,
        label=''
           ) 

    class Meta:
        model = Compressor
        fields = {'Evap_Entering_Water_Temp': ['exact']}

    def __init__(self,*args,**kwargs):
        super(OrderFilter,self).__init__(*args,**kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'  
        self.helper.label_class = 'col-md-6 col-form-label' 
        self.helper.field_class = 'col-md-6'

        Row(
                Column ('date_gt', css_class = 'form-group col-6'),
                #Column (AppendedText('Evap_Leaving_Water_Temp', '°C'), css_class = 'form-group col-6')
                ), 

