# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored additive migration (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_guests --check --dry-run   (on a dev/ephemeral NetBox)
#
# Adds BackupJob (a PVE scheduled vzdump job on one node) and GuestProfile.backup_job (nullable FK:
# the job that backs a guest up). Schema only and purely additive: no existing row changes, and a
# rollback to v0.3.1 leaves a table and a nullable column it never reads.
import django.db.models.deletion
import taggit.managers
import utilities.json
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = (
        ("extras", "__first__"),
        ("dcim", "__first__"),
        ("netbox_guests", "0007_guestprofile_protection"),
    )

    operations = (
        migrations.CreateModel(
            name="BackupJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, blank=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, blank=True, null=True)),
                ("custom_field_data", models.JSONField(
                    blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder)),
                ("job_id", models.CharField(max_length=64)),
                ("storage", models.CharField(max_length=255)),
                ("schedule", models.CharField(max_length=128)),
                ("mode", models.CharField(default="snapshot", max_length=16)),
                ("enabled", models.BooleanField(default=True)),
                ("notes_template", models.CharField(blank=True, max_length=1024)),
                ("repeat_missed", models.BooleanField(default=False)),
                ("notification_mode", models.CharField(default="auto", max_length=32)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("node", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, related_name="backup_jobs",
                    to="dcim.device")),
                ("tags", taggit.managers.TaggableManager(
                    through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={"verbose_name": "Backup Job", "ordering": ["node", "job_id"]},
        ),
        migrations.AddConstraint(
            model_name="backupjob",
            constraint=models.UniqueConstraint(
                fields=("node", "job_id"), name="netbox_guests_backupjob_unique_node_job_id",
            ),
        ),
        migrations.AddField(
            model_name="guestprofile",
            name="backup_job",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name="guests", to="netbox_guests.backupjob",
            ),
        ),
    )
