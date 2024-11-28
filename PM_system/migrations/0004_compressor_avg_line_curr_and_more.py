# Generated by Django 5.0.4 on 2024-11-02 07:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('PM_system', '0003_alter_compressor_evap_water_pd_ft'),
    ]

    operations = [
        migrations.AddField(
            model_name='compressor',
            name='AVg_Line_Curr',
            field=models.CharField(max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='compressor',
            name='Chill_Water_Setpoint',
            field=models.CharField(max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='compressor',
            name='Curr_Lim_Setpoint',
            field=models.CharField(max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='compressor',
            name='Mode',
            field=models.CharField(max_length=15, null=True),
        ),
    ]
