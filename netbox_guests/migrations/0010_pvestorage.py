# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored additive migration (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_guests --check --dry-run   (on a dev/ephemeral NetBox)
#
# Adds PveStorage (a PVE storage definition on one node, today a PBS datastore). Schema only and
# purely additive: no existing row changes, and a rollback to the previous release leaves a table
# it never reads.
import django.core.validators
import django.db.models.deletion
import taggit.managers
import utilities.json
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = (
        ("extras", "__first__"),
        ("dcim", "__first__"),
        ("ipam", "__first__"),
        ("netbox_guests", "0009_guestmount_size_gib"),
    )

    operations = (
        migrations.CreateModel(
            name="PveStorage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, blank=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, blank=True, null=True)),
                ("custom_field_data", models.JSONField(
                    blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder)),
                ("storage_id", models.CharField(max_length=64)),
                ("type", models.CharField(default="pbs", max_length=16)),
                ("port", models.PositiveIntegerField(default=8007)),
                ("datastore", models.CharField(max_length=64)),
                ("username", models.CharField(max_length=128)),
                ("bao_secret_path", models.CharField(max_length=255)),
                ("fingerprint", models.CharField(blank=True, max_length=95, validators=[
                    django.core.validators.RegexValidator(
                        "^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){31}$",
                        "A SHA-256 fingerprint is 32 colon-separated hex octets.",
                    )])),
                ("content", models.CharField(default="backup", max_length=64)),
                ("enabled", models.BooleanField(default=True)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("node", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, related_name="pve_storages",
                    to="dcim.device")),
                ("server", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, related_name="pve_storages",
                    to="ipam.ipaddress")),
                ("tags", taggit.managers.TaggableManager(
                    through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={"verbose_name": "PVE Storage", "ordering": ["node", "storage_id"]},
        ),
        migrations.AddConstraint(
            model_name="pvestorage",
            constraint=models.UniqueConstraint(
                fields=("node", "storage_id"), name="netbox_guests_pvestorage_unique_node_storage_id",
            ),
        ),
    )
