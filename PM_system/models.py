from django.db import models
from django.utils import timezone

# Create your models here. aka we create the containers to store the data , later we will call this container
# This is transformed to sql ready when we do makemigration

class CompressorUnit(models.Model):
      Unit = models.CharField(max_length= 10,default= "")
      def __str__(self): #this is just for showing the string when we call it in python, has nothing to do with database storing
        return self.Unit


class Compressor(models.Model):
    Evap_Entering_Water_Temp = models.IntegerField(null=True) #if not null will not register data to server if no data included
    Evap_Leaving_Water_Temp = models.IntegerField(null=True) # blank true implies that the field is optional
    Evap_Saturated_Rfgt_Temp = models.IntegerField(null=True)
    Evap_Saturated_Rfgt_Pres = models.IntegerField(null=True)
    Evap_Flowswitch_Status = models.CharField(max_length= 15, null=True)
    Evap_Rfgt_Approach_Temp = models.IntegerField(null=True)
    Expansion_Valve_Position = models.IntegerField(null=True)
    Expansion_Valve_Steps = models.IntegerField(null=True)
    Evap_Rfgt_Liquid_Level = models.IntegerField(null=True)
    Evap_Water_PD_FT = models.IntegerField(null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True, default=timezone.now)
    unit = models.ForeignKey(CompressorUnit,on_delete=models.CASCADE,null=True, blank=True)
    Mode = models.CharField(max_length= 15, null=True)
    Chill_Water_Setpoint = models.IntegerField(null=True)
    AVg_Line_Curr = models.IntegerField(null=True)
    Curr_Lim_Setpoint = models.IntegerField(null=True)


class ControlLimit(models.Model):
    """Database-backed default control limits for each plotted variable."""

    variable = models.CharField(max_length=100, unique=True)
    lower_limit = models.FloatField()
    upper_limit = models.FloatField()

    class Meta:
        ordering = ('variable',)
        verbose_name = 'Control limit'
        verbose_name_plural = 'Control limits'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(lower_limit__lte=models.F('upper_limit')),
                name='control_limit_lower_lte_upper',
            ),
        ]

    def __str__(self):
        return self.variable


