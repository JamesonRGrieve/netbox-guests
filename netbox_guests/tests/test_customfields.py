# SPDX-License-Identifier: AGPL-3.0-or-later
"""Asserts the data migration (0002) actually installed the guest custom fields + choice sets on
the right content types. Runs against the migrated test DB (no mocks) -- if the CF model field
names are wrong for the running NetBox, the migration fails at test-DB build and these error
loudly, which is the intended signal."""
from django.test import TestCase
from extras.models import CustomField, CustomFieldChoiceSet
from netbox_guests.customfields import CHOICE_SETS, SPECS


def _object_types(cf):
    return cf.object_types if hasattr(cf, "object_types") else cf.content_types


class CustomFieldInstallTest(TestCase):
    def test_choice_sets_installed(self):
        for name in CHOICE_SETS:
            self.assertTrue(CustomFieldChoiceSet.objects.filter(name=name).exists(), name)

    def test_custom_fields_installed_with_object_types(self):
        for spec in SPECS:
            cf = CustomField.objects.get(name=spec["name"])
            self.assertEqual(cf.type, spec["type"], spec["name"])
            attached = {f"{ot.app_label}.{ot.model}" for ot in _object_types(cf).all()}
            expected = {f"{a}.{m}" for (a, m) in spec["objects"]}
            self.assertEqual(attached, expected, spec["name"])

    def test_guest_type_required_with_choices(self):
        cf = CustomField.objects.get(name="guest_type")
        self.assertTrue(cf.required)
        self.assertIsNotNone(cf.choice_set)

    def test_node_relates_to_device(self):
        cf = CustomField.objects.get(name="node")
        rot = cf.related_object_type
        self.assertEqual((rot.app_label, rot.model), ("dcim", "device"))
