# Generated by Django 2.1.5 on 2019-03-12 23:25

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Word',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('text', models.CharField(db_index=True, max_length=32, verbose_name='Text')),
            ],
            options={
                'verbose_name': 'Word',
                'verbose_name_plural': 'Words',
                'ordering': ['text', '-created'],
            },
        ),
    ]