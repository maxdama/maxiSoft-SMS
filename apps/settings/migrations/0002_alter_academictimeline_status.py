# Generated by Django 3.2.6 on 2022-01-20 21:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps_settings', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='academictimeline',
            name='status',
            field=models.CharField(db_index=True, default='Inactive', max_length=15, null=True),
        ),
    ]
