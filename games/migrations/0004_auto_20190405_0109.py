# Generated by Django 2.1.7 on 2019-04-05 01:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0003_conditiongroup_trigger'),
    ]

    operations = [
        migrations.AlterField(
            model_name='condition',
            name='condition_type',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Has Value'), (1, 'Boolean'), (2, 'Comparison'), (3, 'FSM State')], default=0, verbose_name='Condition Operation'),
        ),
    ]
