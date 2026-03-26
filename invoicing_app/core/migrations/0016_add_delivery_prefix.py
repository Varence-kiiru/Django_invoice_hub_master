# Generated migration to add delivery_prefix field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_savedfilter'),
    ]

    operations = [
        migrations.AddField(
            model_name='companysettings',
            name='delivery_prefix',
            field=models.CharField(
                default='DLV',
                help_text='Prefix for delivery challan numbers (e.g., DLV-2026-0001)',
                max_length=10
            ),
        ),
    ]
