# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored additive migration (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_guests --check --dry-run   (on a dev/ephemeral NetBox)
#
# Adds GuestMount.size_gib: the size of a PVE storage volume the pipeline allocates once and then
# references by volid. Nullable and purely additive: existing (bind-path) mounts keep NULL, and a
# rollback to the previous release leaves a column it never reads.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = (("netbox_guests", "0008_backupjob"),)

    operations = (
        migrations.AddField(
            model_name="guestmount",
            name="size_gib",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                help_text=(
                    "Size in GiB of a PVE storage volume the pipeline allocates once and then references by "
                    "its volid (volume 'storage:subvol-<vmid>-disk-N'). Empty for a host bind path."
                ),
            ),
        ),
    )
