# This migration is kept for backward compatibility
# The actual delivery_prefix field is added in 0016_add_delivery_prefix

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_add_delivery_prefix'),
    ]

    operations = [
        # No operations - all delivery prefix changes handled in 0016_add_delivery_prefix
    ]
