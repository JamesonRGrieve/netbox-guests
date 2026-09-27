# SPDX-License-Identifier: AGPL-3.0-or-later
"""GuestMount filterset tests against a real DB: FK-by-id, FK-by-name, boolean, exact, search."""
from django.test import TestCase
from virtualization.models import VMInterface
from netbox_guests.filtersets import (
    GuestDeviceFilterSet, GuestInterfaceConfigFilterSet, GuestMountFilterSet,
    GuestProfileFilterSet,
)
from netbox_guests.models import (
    GuestDevice, GuestInterfaceConfig, GuestMount, GuestProfile,
)
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


class GuestProfileFilterSetTest(TestCase):
    """Filters the pipeline and the UI actually use: by guest, by node, by kind, by VMID."""

    @classmethod
    def setUpTestData(cls):
        from .test_profile import make_device
        cls.node = make_device("filter-node")
        cls.ct = GuestProfile.objects.create(
            virtual_machine=make_vm("f-ct"), guest_type="container", vmid=7001,
            node=cls.node, storage="local-zfs", onboot=True,
        )
        cls.kvm = GuestProfile.objects.create(
            virtual_machine=make_vm("f-kvm"), guest_type="vm", vmid=7002,
            cpu_type="host", unprivileged=False,
        )

    def _f(self, params):
        return GuestProfileFilterSet(params, queryset=GuestProfile.objects.all()).qs

    def test_by_guest_type(self):
        self.assertEqual(list(self._f({"guest_type": ["container"]})), [self.ct])
        self.assertEqual(list(self._f({"guest_type": ["vm"]})), [self.kvm])

    def test_by_vmid(self):
        self.assertEqual(list(self._f({"vmid": [7002]})), [self.kvm])

    def test_by_node_id_and_name(self):
        self.assertEqual(list(self._f({"node_id": [self.node.pk]})), [self.ct])
        self.assertEqual(list(self._f({"node": [self.node.name]})), [self.ct])

    def test_by_virtual_machine_name(self):
        self.assertEqual(list(self._f({"virtual_machine": ["f-kvm"]})), [self.kvm])

    def test_by_onboot(self):
        self.assertEqual(list(self._f({"onboot": True})), [self.ct])

    def test_search_matches_guest_name_and_storage(self):
        self.assertIn(self.ct, self._f({"q": "local-zfs"}))
        self.assertIn(self.kvm, self._f({"q": "f-kvm"}))


class GuestInterfaceConfigFilterSetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.vm = make_vm("f-iface-vm")
        cls.if0 = VMInterface.objects.create(virtual_machine=cls.vm, name="eth0")
        cls.if1 = VMInterface.objects.create(virtual_machine=make_vm("f-iface-vm2"), name="eth0")
        cls.c0 = GuestInterfaceConfig.objects.create(
            interface=cls.if0, bridge="vmbr0", gateway="192.0.2.1"
        )
        cls.c1 = GuestInterfaceConfig.objects.create(interface=cls.if1, bridge="vmbr77")

    def _f(self, params):
        return GuestInterfaceConfigFilterSet(
            params, queryset=GuestInterfaceConfig.objects.all()
        ).qs

    def test_by_interface_id(self):
        self.assertEqual(list(self._f({"interface_id": [self.if1.pk]})), [self.c1])

    def test_by_virtual_machine_id(self):
        self.assertEqual(list(self._f({"virtual_machine_id": [self.vm.pk]})), [self.c0])

    def test_by_bridge(self):
        self.assertEqual(list(self._f({"bridge": ["vmbr77"]})), [self.c1])

    def test_search_matches_bridge(self):
        self.assertEqual(list(self._f({"q": "vmbr77"})), [self.c1])
