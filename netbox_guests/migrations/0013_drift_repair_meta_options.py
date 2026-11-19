# SPDX-License-Identifier: AGPL-3.0-or-later
# Repairs migration-state drift that predates 0012 (makemigrations --check failed on main): the ordering Meta options
# on BackupJob and PveStorage. State only: no DDL (card 406).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_guests', '0012_guestprofile_manage_journald'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='backupjob',
            options={'ordering': ('node', 'job_id')},
        ),
        migrations.AlterModelOptions(
            name='pvestorage',
            options={'ordering': ('node', 'storage_id')},
        ),
    ]
