# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored initial migration (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_guests --check --dry-run   (on a dev/ephemeral NetBox)
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
    initial = True
    dependencies = [
        # NetBox squashes core app migrations (e.g. virtualization 0001_squashed_0022),
        # so pin to __first__ (resolves to the initial/squashed migration by position).
        ("extras", "__first__"),
        ("virtualization", "__first__"),
    ]
    operations = [
        migrations.CreateModel(
            name="GuestMount",
            fields=[
                *_BASE,
                ("mp", models.PositiveSmallIntegerField()),
                ("volume", models.CharField(max_length=255)),
                ("path", models.CharField(max_length=255)),
                ("read_only", models.BooleanField(default=False)),
                ("virtual_machine", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="guest_mounts", to="virtualization.virtualmachine")),
                _TAGS,
            ],
            options={
                "verbose_name": "Guest Mount",
                "ordering": ["virtual_machine", "mp"],
                "constraints": [models.UniqueConstraint(fields=("virtual_machine", "mp"), name="netbox_guests_guestmount_unique_vm_mp")],
            },
        ),
    ]
