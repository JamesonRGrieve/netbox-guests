# SPDX-License-Identifier: AGPL-3.0-or-later
"""GuestMount model tests against a real DB (no mocks): creation, str/url, the (vm, mp) unique
constraint, and CASCADE when the parent VM is deleted."""
from django.db import transaction
from django.db.utils import IntegrityError
from django.test import TestCase
from netbox_guests.models import GuestDevice, GuestMount
from .utils import make_vm


class GuestMountModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.vm = make_vm("ct-101")

    def test_create_str_and_url(self):
        m = GuestMount.objects.create(
            virtual_machine=self.vm, mp=0, volume="local-zfs:vol-0", path="/data"
        )
        self.assertEqual(str(m), f"{self.vm}: mp0 → /data")
        self.assertIn("/plugins/guests/mounts/", m.get_absolute_url())
        self.assertFalse(m.read_only)

    def test_unique_vm_mp(self):
        GuestMount.objects.create(virtual_machine=self.vm, mp=0, volume="a", path="/a")
        with self.assertRaises(IntegrityError), transaction.atomic():
            GuestMount.objects.create(virtual_machine=self.vm, mp=0, volume="b", path="/b")

    def test_same_mp_different_vm_ok(self):
        other = make_vm("ct-323")
        GuestMount.objects.create(virtual_machine=self.vm, mp=0, volume="a", path="/a")
        GuestMount.objects.create(virtual_machine=other, mp=0, volume="b", path="/b")
        self.assertEqual(GuestMount.objects.filter(mp=0).count(), 2)

    def test_cascade_on_vm_delete(self):
        GuestMount.objects.create(virtual_machine=self.vm, mp=1, volume="a", path="/a")
        self.vm.delete()
        self.assertEqual(GuestMount.objects.count(), 0)


class GuestDeviceModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.vm = make_vm("ct-107")

    def test_create_str_and_url(self):
        d = GuestDevice.objects.create(
            virtual_machine=self.vm, kind="gpu", selector="/dev/nvidia0", index=0,
            cgroup_allow="c 195:* rwm",
        )
        self.assertEqual(str(d), f"{self.vm}: gpu//dev/nvidia0")
        self.assertIn("/plugins/guests/devices/", d.get_absolute_url())
        self.assertEqual(d.index, 0)

    def test_unique_vm_kind_selector_index(self):
        GuestDevice.objects.create(virtual_machine=self.vm, kind="gpu", selector="/dev/nvidia0", index=0)
        with self.assertRaises(IntegrityError), transaction.atomic():
            GuestDevice.objects.create(virtual_machine=self.vm, kind="gpu", selector="/dev/nvidia0", index=0)

    def test_same_selector_different_index_ok(self):
        GuestDevice.objects.create(virtual_machine=self.vm, kind="gpu", selector="/dev/nvidia0", index=0)
        GuestDevice.objects.create(virtual_machine=self.vm, kind="gpu", selector="/dev/nvidia1", index=1)
        self.assertEqual(GuestDevice.objects.filter(kind="gpu").count(), 2)

    def test_cascade_on_vm_delete(self):
        GuestDevice.objects.create(virtual_machine=self.vm, kind="usb", selector="2341:0043")
        self.vm.delete()
        self.assertEqual(GuestDevice.objects.count(), 0)
