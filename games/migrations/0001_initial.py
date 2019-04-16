# Generated by Django 2.1.7 on 2019-04-16 02:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('gamedefinitions', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Condition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('condition_type', models.PositiveSmallIntegerField(choices=[(0, 'Has Value'), (1, 'Boolean'), (2, 'Comparison'), (3, 'FSM State')], default=0, verbose_name='Condition Operation')),
                ('comparison_type', models.PositiveSmallIntegerField(choices=[(0, '=='), (1, '!='), (2, '>'), (3, '<'), (4, '>='), (5, '<=')], default=0, verbose_name='Comparison Operation')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ConditionGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('boolean_op', models.PositiveSmallIntegerField(choices=[(0, 'OR'), (1, 'AND')], default=0, verbose_name='Boolean Operation')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('code', models.SlugField(max_length=16, verbose_name='Code')),
                ('game_definition', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gamedefinitions.GameDefinition')),
            ],
            options={
                'verbose_name': 'Game',
                'ordering': ['-created'],
                'verbose_name_plural': 'Games',
            },
        ),
        migrations.CreateModel(
            name='MixedValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('integer', models.IntegerField(blank=True, default=None, null=True, verbose_name='Integer')),
                ('string', models.CharField(blank=True, default=None, max_length=255, null=True, verbose_name='String')),
                ('boolean', models.NullBooleanField(default=None, verbose_name='Boolean')),
                ('float', models.FloatField(blank=True, default=None, null=True, verbose_name='Float')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('key', models.SlugField(max_length=255, verbose_name='Key')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='Object ID')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.ContentType')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parameters', to='games.Game')),
            ],
        ),
        migrations.CreateModel(
            name='StateMachine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('current_state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='gamedefinitions.State')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='state_machines', to='games.Game')),
                ('previous_state', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='gamedefinitions.State')),
                ('root_state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='gamedefinitions.State')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Transition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('reason', models.SlugField(max_length=32, verbose_name='Reason')),
                ('from_state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='gamedefinitions.State')),
                ('state_machine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transitions', to='games.StateMachine')),
                ('to_state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='gamedefinitions.State')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Trigger',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('active', models.BooleanField(db_index=True, default=True, verbose_name='Active')),
                ('repeats', models.BooleanField(default=False, verbose_name='Repeats')),
                ('trigger_count', models.PositiveSmallIntegerField(default=0, verbose_name='Trigger Count')),
                ('condition_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='triggers', to='games.ConditionGroup')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='triggers', to='games.Game')),
                ('rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='gamedefinitions.Rule')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
