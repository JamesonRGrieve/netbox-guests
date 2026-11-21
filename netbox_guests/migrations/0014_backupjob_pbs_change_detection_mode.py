# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored additive migration (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_guests --check --dry-run   (on a dev/ephemeral NetBox)
#
# Adds BackupJob.pbs_change_detection_mode: how container backups to PBS find changed files
# (PVE pbs-change-detection-mode; operator 2026-11-21, card 180). Blank on every existing row, which
# keeps PVE's default; db_default keeps the column insertable by code that predates it.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = (("netbox_guests", "0013_drift_repair_meta_options"),)

    operations = (
        migrations.AddField(
            model_name="backupjob",
            name="pbs_change_detection_mode",
            field=models.CharField(
                max_length=16,
                blank=True,
                default="",
                db_default="",
                help_text="How container backups to PBS find changed files; blank keeps PVE's default (legacy). "
                "metadata reuses unchanged files from the previous snapshot.",
            ),
        ),
    )
