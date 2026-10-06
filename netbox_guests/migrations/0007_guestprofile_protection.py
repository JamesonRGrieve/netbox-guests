# SPDX-License-Identifier: AGPL-3.0-or-later
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_guests", "0006_custom_fields_to_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="guestprofile",
            name="protection",
            field=models.BooleanField(
                default=False,
                help_text="PVE protection flag: the guest and its disks cannot be removed until "
                "it is cleared. Set on control-plane guests.",
            ),
        ),
    ]
