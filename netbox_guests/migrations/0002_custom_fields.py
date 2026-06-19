# SPDX-License-Identifier: AGPL-3.0-or-later
# Data migration: install the guest custom fields on virtualization.virtualmachine /
# .vminterface (see netbox_guests.customfields). Split from 0001 so the CF install can depend on
# the LATEST extras migration (CustomFieldChoiceSet + CustomField tables must exist) without
# coupling the GuestMount model migration to it. Verify on an ephemeral NetBox via a test run
# (tests/test_customfields.py) -- the CF model field names target NetBox 4.6.
from django.db import migrations
from ..customfields import install, uninstall


class Migration(migrations.Migration):
    dependencies = [
        ("netbox_guests", "0001_initial"),
        ("contenttypes", "0001_initial"),
        # dcim + virtualization core migrations are squashed in NetBox 4.6 → __first__.
        ("dcim", "__first__"),
        ("virtualization", "__first__"),
        ("extras", "__latest__"),
    ]
    operations = [
        migrations.RunPython(install, uninstall),
    ]
