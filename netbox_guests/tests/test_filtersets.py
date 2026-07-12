# SPDX-License-Identifier: AGPL-3.0-or-later
"""GuestMount filterset tests against a real DB: FK-by-id, FK-by-name, boolean, exact, search."""
from django.test import TestCase
from netbox_guests.filtersets import GuestDeviceFilterSet, GuestMountFilterSet
from netbox_guests.models import GuestDevice, GuestMount
from .utils import make_vm


class GuestMountFilterSetTest(TestCase):
    queryset = GuestMount.objects.all()

    @classmethod
    def setUpTestData(cls):
        cls.vm1 = make_vm("fvm1")
        cls.vm2 = make_vm("fvm2", cluster_name="backup")
        GuestMount.objects.create(virtual_machine=cls.vm1, mp=0, volume="local:0", path="/data")
        GuestMount.objects.create(virtual_machine=cls.vm1, mp=1, volume="nfs:share", path="/srv", read_only=True)
        GuestMount.objects.create(virtual_machine=cls.vm2, mp=0, volume="local:0", path="/var")

    def _f(self, params):
        return GuestMountFilterSet(params, self.queryset).qs

    def test_virtual_machine_id(self):
        self.assertEqual(self._f({"virtual_machine_id": [self.vm1.pk]}).count(), 2)

    def test_virtual_machine_name(self):
        self.assertEqual(self._f({"virtual_machine": ["fvm2"]}).count(), 1)

    def test_read_only(self):
        self.assertEqual(self._f({"read_only": True}).count(), 1)

    def test_mp(self):
        # query-param values arrive as strings; int 0 is falsy and skips the filter
        self.assertEqual(self._f({"mp": "0"}).count(), 2)

    def test_search_volume(self):
        self.assertEqual(self._f({"q": "nfs"}).count(), 1)


class GuestDeviceFilterSetTest(TestCase):
    queryset = GuestDevice.objects.all()

    @classmethod
    def setUpTestData(cls):
        cls.vm1 = make_vm("dfvm1")
        cls.vm2 = make_vm("dfvm2", cluster_name="backup")
        GuestDevice.objects.create(virtual_machine=cls.vm1, kind="gpu", selector="/dev/nvidia0", index=0, cgroup_allow="c 195:* rwm")
        GuestDevice.objects.create(virtual_machine=cls.vm1, kind="gpu", selector="/dev/nvidia1", index=1, description="second gpu")
        GuestDevice.objects.create(virtual_machine=cls.vm2, kind="usb", selector="2341:0043", index=0)

    def _f(self, params):
        return GuestDeviceFilterSet(params, self.queryset).qs

    def test_virtual_machine_id(self):
        self.assertEqual(self._f({"virtual_machine_id": [self.vm1.pk]}).count(), 2)

    def test_virtual_machine_name(self):
        self.assertEqual(self._f({"virtual_machine": ["dfvm2"]}).count(), 1)

    def test_kind(self):
        self.assertEqual(self._f({"kind": ["gpu"]}).count(), 2)

    def test_selector(self):
        self.assertEqual(self._f({"selector": ["2341:0043"]}).count(), 1)

    def test_search_selector(self):
        self.assertEqual(self._f({"q": "nvidia1"}).count(), 1)

    def test_search_description(self):
        self.assertEqual(self._f({"q": "second gpu"}).count(), 1)
