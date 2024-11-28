from django.db import models
from datetime import datetime 

# Create your models here.
class CompressorUnit(models.Model):
      Unit = models.CharField(max_length= 10,default= "")
      def __str__(self):
        return self.Unit


class Compressor(models.Model):
    Evap_Entering_Water_Temp = models.IntegerField(max_length= 100, null=True) #if not null will not register data to server if no data included
    Evap_Leaving_Water_Temp = models.IntegerField(max_length= 3, null=True) # blank true implies that the field is optional
    Evap_Saturated_Rfgt_Temp = models.IntegerField(max_length= 15, null=True)
    Evap_Saturated_Rfgt_Pres = models.IntegerField(max_length= 15,null=True)
    Evap_Flowswitch_Status = models.CharField(max_length= 15, null=True)
    Evap_Rfgt_Approach_Temp = models.IntegerField(max_length= 15, null=True)
    Expansion_Valve_Position = models.IntegerField(max_length= 15, null=True)
    Expansion_Valve_Steps = models.IntegerField(max_length= 15,null=True)
    Evap_Rfgt_Liquid_Level = models.IntegerField(max_length= 15, null=True)
    Evap_Water_PD_FT = models.IntegerField(max_length= 15, null=True,blank=True)
    date = models.DateTimeField(null = True, blank=True,default=datetime.now)
    unit = models.ForeignKey(CompressorUnit,on_delete=models.CASCADE,null=True, blank=True)
    Mode = models.CharField(max_length= 15, null=True)
    Chill_Water_Setpoint = models.IntegerField(max_length= 15, null=True)
    AVg_Line_Curr = models.IntegerField(max_length= 15, null=True)
    Curr_Lim_Setpoint = models.IntegerField(max_length= 15, null=True)


