from django import forms
from .models import Compressor
from datetime import date
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import AppendedText,InlineRadios
from crispy_forms.layout import Layout,Fieldset,Submit,Field,Div,Column,Row,HTML,Button

class CompressorForm(forms.ModelForm):

    FLOW_CHOICES = [
        ('Flow', 'Flow'),
        ('No flow', 'No Flow')]
    
    MODE_CHOICS = [
        ('Run', 'Run'),
        ('Offline', 'Offline'),
    ]
    
    Evap_Flowswitch_Status = forms.ChoiceField(
        choices=FLOW_CHOICES, 
        widget=forms.RadioSelect(attrs={'class': 'form-check-inline'}) 
    )

    Mode = forms.ChoiceField(
        choices=MODE_CHOICS, 
        widget=forms.RadioSelect(attrs={'class': 'form-check-inline'}) 
    )

    
    class Meta:
        model = Compressor
        fields = "__all__"

    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), initial=date.today)
    

    def __init__(self,*args,**kwargs):
        super(CompressorForm,self).__init__(*args,**kwargs)
        self.fields['unit'].empty_label="Select"
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'  
        self.helper.label_class = 'col-md-6 col-form-label'  # Proper label class
        self.helper.field_class = 'col-md-6'
        self.helper.layout = Layout(
               Row(
                Column('date', css_class='form-group col-md-6  '),
                Column('unit', css_class='form-group col-md-6  '),
                css_class='form-row'
            ),
            HTML(""" <hr> </hr>
                        <div class="display-6"> </div>
                        <div class="display-6"> Main Tab </div> """),
            Row(
                Column(InlineRadios('Mode'), css_class='form-group col-md-6  '),
                Column(AppendedText('Chill_Water_Setpoint', 'F'), css_class='form-group col-md-6  '),
            ),
            Row(
                Column(AppendedText('AVg_Line_Curr', '% RLA'), css_class='form-group col-md-6  '),
                Column(AppendedText('Curr_Lim_Setpoint', '% RLA'), css_class='form-group col-md-6')
            ),
            
            HTML(""" <hr> </hr>
                        <div class="display-6"> </div>
                        <div class="display-6"> Evaporator </div> """),

            Row(
                Column (AppendedText('Evap_Entering_Water_Temp', '°C'), css_class = 'form-group col-6'),
                Column (AppendedText('Evap_Leaving_Water_Temp', '°C'), css_class = 'form-group col-6')
                ),

             Row(
                Column (AppendedText('Evap_Saturated_Rfgt_Temp', '°C'), css_class = 'form-group col-6'),
                Column (AppendedText('Evap_Saturated_Rfgt_Pres', 'Pa'), css_class = 'form-group col-6')
                ),
             Row(
                Column (InlineRadios('Evap_Flowswitch_Status'), css_class = 'form-group col-6'),
                Column (AppendedText('Evap_Rfgt_Approach_Temp', '°C'), css_class = 'form-group col-6')
                ),
             Row(
                Column (AppendedText('Expansion_Valve_Position', '%'), css_class = 'form-group col-6'),
                Column (AppendedText('Expansion_Valve_Steps', ''), css_class = 'form-group col-6')
                ),
            Row(
                Column (AppendedText('Evap_Rfgt_Liquid_Level', 'mm'), css_class = 'form-group col-6'),
                ),
            Row(
                Column (HTML(""" <button type="submit" class="btn btn-success w-100"><i class="fa fa-id-card-o"></i></i>Submit</button>"""), css_class = 'form-group col-6'),
                Column(HTML("""<a href= "{% url "PM_filter" %}" class="btn btn-secondary w-100 ">
                                <i class = "fas fa-stream"></i> Back to list
                                </a>"""), css_class = 'form-group col-6')
                ),
                )

    
                
                
        
        
        
    
 