from django.shortcuts import render,redirect
from . models import Compressor
from .forms import CompressorForm
from .filters import OrderFilter
import plotly.express as px 
from .forms2 import DateForm
from django.http import HttpResponse
from openpyxl import Workbook
from io import BytesIO
import numpy as np
from sklearn.metrics import r2_score


def PM_list(request):
     context = {'compressor_list' : Compressor.objects.all() }
     return render(request,"PM_system/compressor_list.html",context) #html link 

# Filter
def PM_filter(request):
    # Create the filter object and pass the filtered queryset to the context
    form_filter = OrderFilter(request.GET, queryset=Compressor.objects.all().order_by('-date')) #performs the filtering process

    if 'export' in request.GET:
        return export_excel(form_filter) 
    
    context = {
        'myFilter': form_filter, 
        'compressor_list' : form_filter.qs}
        
    return render(request, "PM_system/compressor_filter.html", context)

# Form
def compressor_form(request,id=0):
         if request.method == "GET":
            if id==0:
                form = CompressorForm()
            else:
                forms = Compressor.objects.get(pk=id)
                form = CompressorForm(instance=forms)  #forms
            return render (request,"PM_system/compressor_form.html",{'form':form})
         else:
             form = CompressorForm(request.POST) 
             if request.method == "POST":
                print(request.POST) 
                if form.is_valid():
                 form.save()
                 print("pass")
                else:
                 print("form.errors")

             return redirect ('/compressor')
         
# Excel Sample
def export_excel(form_filter):
    # Create an in-memory workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Chiller Data"

    # Add headers to the Excel sheet
    headers = ['Evap Entering Water Temp', 'Evap Leaving Water Temp', 'Evap Saturated Rfgt Temp', 
               'Evap Saturated Rfgt Pres', 'Evap Flowswitch Status', 'Evap Rfgt Approach Temp']
    ws.append(headers)

    # Use filtered data from form_filter.qs
    data = form_filter.qs
    for d in data:
        ws.append([
            d.Evap_Entering_Water_Temp,
            d.Evap_Leaving_Water_Temp,
            d.Evap_Saturated_Rfgt_Temp,
            d.Evap_Saturated_Rfgt_Pres,
            d.Evap_Flowswitch_Status,
            d.Evap_Rfgt_Approach_Temp
        ])

    # Save the workbook to an in-memory bytes buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    # Create the HTTP response and attach the Excel file
    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="compressor_data.xlsx"'

    return response

def compressor_delete(request):
    return

# Dict Select Function
def Select(dicz, keyz):
    for i in dicz:
      try: 
         if i == keyz:
            labelz = dicz[i]
            return labelz
      except:
          return "Error"

# Plot Code
def PM_plot(request):
   
   plot = Compressor.objects.all()
   units = request.GET.get('unit')
   total_count = plot.count()

   if units:
    if units == "0":
        plot = Compressor.objects.all()
    else:
        plot = Compressor.objects.filter(unit_id=units)

   start = request.GET.get('start')
   end = request.GET.get('end')

   if start:
       plot = plot.filter(date__gte=start)
   if end:
       plot = plot.filter(date__lte=end)

   var = request.GET.get('var')

   dict1 = {"Evap_Entering_Water_Temp" :"Evap Entering Water Temp (F)",
             "Evap_Leaving_Water_Temp":"Evap Leaving Water Temp (F)",
             "Evap_Saturated_Rfgt_Temp":"Evap Saturated Rfgt Temp (F)",
             "Evap_Saturated_Rfgt_Pres":"Evap Saturated Rfgt Pres (psi)",
             "Evap_Rfgt_Approach_Temp":"Evap Rfgt Approach Temp (F)",
             "Expansion_Valve_Position":"Expansion Valve Position (%)",
             "Expansion_Valve_Steps":"Expansion Valve Steps (mm)",
             "Evap_Rfgt_Liquid_Level":"Evap Rfgt Liquid Level (%)"}
   
   dict_UL = {"Evap_Entering_Water_Temp" : 15,
             "Evap_Leaving_Water_Temp": 15,
             "Evap_Saturated_Rfgt_Temp":8,
             "Evap_Saturated_Rfgt_Pres":256,
             "Evap_Rfgt_Approach_Temp":5,
             "Expansion_Valve_Position":45,
             "Expansion_Valve_Steps":1745,
             "Evap_Rfgt_Liquid_Level":5}
   
   dict_LL = {"Evap_Entering_Water_Temp" :5,
             "Evap_Leaving_Water_Temp":5,
             "Evap_Saturated_Rfgt_Temp":4,
             "Evap_Saturated_Rfgt_Pres":250,
             "Evap_Rfgt_Approach_Temp":0,
             "Expansion_Valve_Position":25,
            "Expansion_Valve_Steps":1735,
             "Evap_Rfgt_Liquid_Level":0}
   
   label = Select(dict1,var)
   
   if var :
     n = str(str(var))
   else :
     n = "Evap_Entering_Water_Temp"
     label = "Evap Entering Water Temp (F)"
     var = "Evap_Entering_Water_Temp"
   
   
   
   y = [getattr(c,n) for c in plot]  

   f_y = [value for value in y if value is not None]
   f_y = np.array(f_y)


   min = np.min(f_y)
   max = np.max(f_y)
   avg = np.mean(f_y)
   std1 = np.std(f_y) 

   target = np.full(f_y.shape,avg)
   r2 = r2_score(f_y,target)
   print(round(r2,6))

   count = 0 

   unit_label = { "1": "Trane-1", "2": "Trane-2", "3": "Trane-3"}

   custom_color = ["#f2360e", "#15f20e", "#f2a60e"]

   fig = px.scatter(
       x = [ c.date for c in plot],
       y = [getattr(c,n) for c in plot],
       title = label,
       #color= unit_label, 
       color = [ str(c.unit_id) for c in plot],
       labels = {"x": "Date", "y": label , "color": "Unit"},
       trendline="lowess", 
       color_discrete_sequence= custom_color,
   )
   

   fig.for_each_trace(lambda t: t.update(name={
    "1": "Trane -1",
    "2": "Trane -2",
    "3": "Trane -3"
    }.get(t.name, t.name))) 
   
   fig.update_layout(title={
      'font_size' : 22,
      'xanchor' :'center',
      'x' :0.5
   })
   
   UL = Select(dict_UL,var)
   LL = Select(dict_LL,var)

   print(f"UL and LL value {UL,LL}")

   for i in f_y:
       if i > UL or i < LL:
           count += 1

   Percentage = ((total_count- count) / (total_count))*100

   fig.add_hline(y=UL,
                  line_dash="dash",  
                  line_color="blue",
                  annotation_text= 'UCL',
                  annotation_position='top right', 
                  annotation_font_color='blue')
   
   fig.add_hline(y=LL,
                  line_dash="dash",  
                  line_color="blue",
                  annotation_text= 'LCL',
                  annotation_position='bottom right', 
                  annotation_font_color='blue')


   chart = fig.to_html()
   context = {'chart': chart ,
            "form2":DateForm(),
            "min":round(min,2),
            "max":round(max,2),  
            "avg":round(avg,2),
            "std1":round(std1,2),
            "count":round(count,2),
            "var":var,
            "percentage":round(Percentage,2)}
  
   
   return render(request,"PM_system/PM_plot.html",context)

def Home(request):
     return render(request,"PM_system/Home.html")

def compressor_delete(request,id):
    data = Compressor.objects.get(pk=id)
    data.delete()
    return redirect('/compressor/filter')


  