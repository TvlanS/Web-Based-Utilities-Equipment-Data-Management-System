from django.db import migrations, models


CONTROL_LIMITS = [
    ('Evap_Entering_Water_Temp', 5, 15),
    ('Evap_Leaving_Water_Temp', 5, 15),
    ('Evap_Saturated_Rfgt_Temp', 4, 8),
    ('Evap_Saturated_Rfgt_Pres', 250, 256),
    ('Evap_Rfgt_Approach_Temp', 0, 5),
    ('Expansion_Valve_Position', 25, 45),
    ('Expansion_Valve_Steps', 1735, 1745),
    ('Evap_Rfgt_Liquid_Level', 0, 5),
]


def create_default_limits(apps, schema_editor):
    ControlLimit = apps.get_model('PM_system', 'ControlLimit')
    ControlLimit.objects.bulk_create([
        ControlLimit(variable=variable, lower_limit=lower, upper_limit=upper)
        for variable, lower, upper in CONTROL_LIMITS
    ])


def remove_default_limits(apps, schema_editor):
    ControlLimit = apps.get_model('PM_system', 'ControlLimit')
    ControlLimit.objects.filter(variable__in=[item[0] for item in CONTROL_LIMITS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('PM_system', '0007_alter_compressor_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='ControlLimit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variable', models.CharField(max_length=100, unique=True)),
                ('lower_limit', models.FloatField()),
                ('upper_limit', models.FloatField()),
            ],
            options={
                'verbose_name': 'Control limit',
                'verbose_name_plural': 'Control limits',
                'ordering': ('variable',),
            },
        ),
        migrations.AddConstraint(
            model_name='controllimit',
            constraint=models.CheckConstraint(
                condition=models.Q(('lower_limit__lte', models.F('upper_limit'))),
                name='control_limit_lower_lte_upper',
            ),
        ),
        migrations.RunPython(create_default_limits, remove_default_limits),
    ]
