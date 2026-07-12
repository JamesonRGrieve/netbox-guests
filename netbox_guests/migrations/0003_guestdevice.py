# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored additive migration (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_guests --check --dry-run   (on a dev/ephemeral NetBox)
# Adds GuestDevice: the per-guest passthrough-device SoT (GPU / USB / PCI / tty), the sibling of
# GuestMount for host devices realized into the CT as native devN or raw lxc.cgroup2/mount lines.
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
        ("netbox_guests", "0002_custom_fields"),
        # virtualization core migrations are squashed in NetBox 4.6 → __first__.
        ("virtualization", "__first__"),
    ]
    operations = [
        migrations.CreateModel(
            name="GuestDevice",
            fields=[
                *_BASE,
                ("kind", models.CharField(max_length=16)),
                ("selector", models.CharField(max_length=255)),
                ("index", models.PositiveSmallIntegerField(default=0)),
                ("cgroup_allow", models.CharField(blank=True, max_length=255)),
                ("mount_entry", models.CharField(blank=True, max_length=255)),
                ("mode", models.CharField(blank=True, max_length=16)),
                ("gid", models.PositiveIntegerField(blank=True, null=True)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("virtual_machine", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="devices", to="virtualization.virtualmachine")),
                _TAGS,
            ],
            options={
                "verbose_name": "Guest Device",
                "ordering": ["virtual_machine", "kind", "index", "selector"],
                "constraints": [models.UniqueConstraint(fields=("virtual_machine", "kind", "selector", "index"), name="netbox_guests_guestdevice_unique_vm_kind_selector_index")],
            },
        ),
    ]
