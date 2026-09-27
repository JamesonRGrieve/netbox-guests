# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored additive migration (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_guests --check --dry-run   (on a dev/ephemeral NetBox)
#
# Adds the two models that supersede this plugin's per-VM and per-VMInterface custom fields:
# GuestProfile (OneToOne VirtualMachine) and GuestInterfaceConfig (OneToOne VMInterface). Schema
# only -- 0006 copies the existing custom-field values into these rows, and 0007 removes the
# custom fields once nothing reads them.
import django.contrib.postgres.fields
import django.core.serializers.json
import django.db.models.deletion
import taggit.managers
import utilities.json
from django.db import migrations, models

_BASE = [
    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
    ("created", models.DateTimeField(auto_now_add=True, blank=True, null=True)),
    ("last_updated", models.DateTimeField(auto_now=True, blank=True, null=True)),
    ("custom_field_data", models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder)),
]
_TAGS = ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag"))


class Migration(migrations.Migration):
    dependencies = [
        ("extras", "__first__"),
        ("netbox_guests", "0004_guestmount_backup"),
        ("dcim", "__first__"),
        # virtualization core migrations are squashed in NetBox 4.6 -> __first__.
        ("virtualization", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            name="GuestProfile",
            fields=_BASE + [
                ("guest_type", models.CharField(max_length=16)),
                ("vmid", models.PositiveIntegerField(blank=True, null=True)),
                ("pool", models.CharField(blank=True, max_length=128)),
                ("storage", models.CharField(blank=True, max_length=255)),
                ("onboot", models.BooleanField(default=False)),
                ("start", models.BooleanField(default=False)),
                ("description_template", models.TextField(blank=True)),
                ("bao_secret_path", models.CharField(blank=True, max_length=255)),
                ("has_admin_password", models.BooleanField(default=False)),
                ("has_admin_token", models.BooleanField(default=False)),
                ("has_db_password", models.BooleanField(default=False)),
                ("has_secret_key", models.BooleanField(default=False)),
                ("swap", models.PositiveIntegerField(blank=True, null=True)),
                ("unprivileged", models.BooleanField(default=True)),
                ("features", django.contrib.postgres.fields.ArrayField(
                    base_field=models.CharField(max_length=32), blank=True, default=list, size=None)),
                ("ostemplate", models.CharField(blank=True, max_length=255)),
                ("template", models.CharField(blank=True, max_length=255)),
                ("image", models.CharField(blank=True, max_length=255)),
                ("iso", models.CharField(blank=True, max_length=255)),
                ("bios", models.CharField(blank=True, max_length=16)),
                ("cpu_type", models.CharField(blank=True, max_length=64)),
                ("sockets", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("numa", models.BooleanField(default=False)),
                ("agent", models.BooleanField(default=False)),
                ("cloud_init", models.BooleanField(default=False)),
                ("node", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="hosted_guests", to="dcim.device")),
                ("sandbox_of", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="sandbox_guests", to="virtualization.virtualmachine")),
                ("virtual_machine", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="guest_profile", to="virtualization.virtualmachine")),
                _TAGS,
            ],
            options={"verbose_name": "Guest Profile", "ordering": ["virtual_machine"]},
        ),
        migrations.AddConstraint(
            model_name="guestprofile",
            constraint=models.UniqueConstraint(
                condition=models.Q(("vmid__isnull", False)),
                fields=("vmid",), name="netbox_guests_guestprofile_unique_vmid",
            ),
        ),
        migrations.CreateModel(
            name="GuestInterfaceConfig",
            fields=_BASE + [
                ("bridge", models.CharField(blank=True, max_length=64)),
                ("gateway", models.GenericIPAddressField(blank=True, null=True)),
                ("interface", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="guest_config", to="virtualization.vminterface")),
                _TAGS,
            ],
            options={"verbose_name": "Guest Interface Config", "ordering": ["interface"]},
        ),
    ]
