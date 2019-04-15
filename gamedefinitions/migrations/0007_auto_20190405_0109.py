# Generated by Django 2.1.7 on 2019-04-05 01:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gamedefinitions', '0006_remove_gamedefinition_root_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='gamedefinition',
            name='rules',
            field=models.ManyToManyField(blank=True, related_name='game_definitions', to='gamedefinitions.Rule'),
        ),
        migrations.AddField(
            model_name='gamedefinition',
            name='states',
            field=models.ManyToManyField(blank=True, related_name='game_definitions', to='gamedefinitions.State'),
        ),
        migrations.AlterField(
            model_name='gamedefinition',
            name='first_rule',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='gamedefinitions.Rule'),
        ),
    ]