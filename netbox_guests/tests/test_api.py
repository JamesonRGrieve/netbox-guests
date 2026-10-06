# SPDX-License-Identifier: AGPL-3.0-or-later
"""REST API CRUD tests (real DB + real API client, no mocks). Composes the explicit CRUD mixins
(no GraphQL type shipped). The (vm, mp) unique constraint means each row needs a distinct mp."""
from utilities.testing import APIViewTestCases
from virtualization.models import VMInterface
from netbox_guests.models import (
    GuestDevice, GuestInterfaceConfig, GuestMount, GuestProfile,
)
from .test_profile import make_device
from .utils import make_vm


class _PluginAPI:
    """Plugin API views live under the `plugins-api:` namespace. A plain mixin, not a TestCase,
    so the runner never collects it as a model-less test class."""

    view_namespace = "plugins-api:netbox_guests"


_CRUD = (
    _PluginAPI,
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
)


class GuestMountAPITest(*_CRUD):
    model = GuestMount
    brief_fields = ["display", "id", "mp", "path", "url", "virtual_machine"]
    bulk_update_data = {"read_only": True}

    @classmethod
    def setUpTestData(cls):
        vm = make_vm("api-vm")
        GuestMount.objects.bulk_create([
            GuestMount(virtual_machine=vm, mp=0, volume="local:0", path="/a"),
            GuestMount(virtual_machine=vm, mp=1, volume="local:1", path="/b"),
            GuestMount(virtual_machine=vm, mp=2, volume="local:2", path="/c"),
        ])
        cls.create_data = [
            {"virtual_machine": vm.pk, "mp": 10, "volume": "local:10", "path": "/x"},
            {
                "virtual_machine": vm.pk, "mp": 11, "volume": "local:11", "path": "/y",
                "read_only": True,
            },
            {"virtual_machine": vm.pk, "mp": 12, "volume": "local:12", "path": "/z"},
        ]


class GuestDeviceAPITest(*_CRUD):
    model = GuestDevice
    brief_fields = ["display", "id", "index", "kind", "selector", "url", "virtual_machine"]
    bulk_update_data = {"mode": "0660"}

    @classmethod
    def setUpTestData(cls):
        vm = make_vm("api-dev-vm")
        GuestDevice.objects.bulk_create([
            GuestDevice(
                virtual_machine=vm, kind="gpu", selector="/dev/nvidia0", index=0,
                cgroup_allow="c 195:* rwm",
            ),
            GuestDevice(
                virtual_machine=vm, kind="gpu", selector="/dev/nvidia1", index=1,
                cgroup_allow="c 195:* rwm",
            ),
            GuestDevice(virtual_machine=vm, kind="usb", selector="2341:0043", index=0),
        ])
        cls.create_data = [
            {"virtual_machine": vm.pk, "kind": "gpu", "selector": "/dev/nvidiactl", "index": 0},
            {"virtual_machine": vm.pk, "kind": "pci", "selector": "0000:07:00.0", "index": 0},
            {
                "virtual_machine": vm.pk, "kind": "tty", "selector": "/dev/ttyUSB0", "index": 0,
                "cgroup_allow": "c 188:* rwm",
            },
        ]


class GuestProfileAPITest(*_CRUD):
    model = GuestProfile
    brief_fields = ["display", "guest_type", "id", "url", "virtual_machine", "vmid"]
    bulk_update_data = {"onboot": True}

    @classmethod
    def setUpTestData(cls):
        node = make_device("api-node")
        for i, name in enumerate(("api-p1", "api-p2", "api-p3")):
            GuestProfile.objects.create(
                virtual_machine=make_vm(name), guest_type="container",
                vmid=9000 + i, node=node, storage="local-zfs",
            )
        cls.create_data = [
            {"virtual_machine": make_vm("api-p4").pk, "guest_type": "container", "vmid": 9100},
            {"virtual_machine": make_vm("api-p5").pk, "guest_type": "vm", "vmid": 9101,
             "bios": "ovmf", "cpu_type": "host", "unprivileged": False},
            {"virtual_machine": make_vm("api-p6").pk, "guest_type": "container",
             "storage": "local-lvm"},
        ]


class GuestInterfaceConfigAPITest(*_CRUD):
    model = GuestInterfaceConfig
    brief_fields = ["bridge", "display", "gateway", "id", "interface", "url"]
    bulk_update_data = {"bridge": "vmbr9"}

    @classmethod
    def setUpTestData(cls):
        vm = make_vm("api-iface-vm")
        for n in range(3):
            GuestInterfaceConfig.objects.create(
                interface=VMInterface.objects.create(virtual_machine=vm, name=f"eth{n}"),
                bridge=f"vmbr{n}",
            )
        cls.create_data = [
            {"interface": VMInterface.objects.create(virtual_machine=vm, name="eth10").pk,
             "bridge": "vmbr0", "gateway": "192.0.2.1"},
            {"interface": VMInterface.objects.create(virtual_machine=vm, name="eth11").pk,
             "bridge": "vmbr1"},
            {"interface": VMInterface.objects.create(virtual_machine=vm, name="eth12").pk,
             "gateway": "198.51.100.1"},
        ]
