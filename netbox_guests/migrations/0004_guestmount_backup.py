# SPDX-License-Identifier: AGPL-3.0-or-later
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("netbox_guests", "0003_guestdevice")]

    operations = [
        migrations.AddField(
            model_name="guestmount",
            name="backup",
            field=models.BooleanField(default=True, help_text="Include in vzdump backups (backup=1)."),
        ),
    ]
