# SPDX-License-Identifier: AGPL-3.0-or-later
"""GuestProfile / GuestInterfaceConfig tests against a real DB (no mocks).

Covers what the custom fields could not enforce and is therefore the whole point of the models:
the fleet-wide unique VMID, the node FK refusing to vanish under its guests, ``clean()`` rejecting
intent that belongs to the other guest kind, the sandbox self-reference guard, and CASCADE from
the parent VM / interface.
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError, ProtectedError
from django.test import TestCase
from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from virtualization.models import VMInterface
from netbox_guests.choices import GuestTypeChoices, LxcFeatureChoices, PveBiosChoices
from netbox_guests.models import GuestInterfaceConfig, GuestProfile
from .utils import make_vm


def make_device(name):
    site, _ = Site.objects.get_or_create(name="House", slug="house")
    mfr, _ = Manufacturer.objects.get_or_create(name="Generic", slug="generic")
    dtype, _ = DeviceType.objects.get_or_create(manufacturer=mfr, model="PVE Node", slug="pve-node")
    role, _ = DeviceRole.objects.get_or_create(name="Hypervisor", slug="hypervisor")
    return Device.objects.create(name=name, site=site, device_type=dtype, role=role)


class GuestProfileModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.vm = make_vm("ct-101")
        cls.node = make_device("core")

    def test_create_str_and_url(self):
        p = GuestProfile.objects.create(
            virtual_machine=self.vm, guest_type=GuestTypeChoices.CONTAINER,
            vmid=101, node=self.node, storage="local-zfs", onboot=True,
        )
        self.assertEqual(str(p), f"{self.vm}: Container (LXC)")
        self.assertIn("/plugins/guests/profiles/", p.get_absolute_url())
        self.assertTrue(p.unprivileged, "unprivileged must default true — privileged is opt-out")
        self.assertEqual(p.features, [])

    def test_vmid_unique_fleet_wide(self):
        GuestProfile.objects.create(
            virtual_machine=self.vm, guest_type=GuestTypeChoices.CONTAINER, vmid=101
        )
        other = make_vm("ct-102")
        with self.assertRaises(IntegrityError), transaction.atomic():
            GuestProfile.objects.create(
                virtual_machine=other, guest_type=GuestTypeChoices.CONTAINER, vmid=101
            )

    def test_null_vmids_do_not_collide(self):
        GuestProfile.objects.create(
            virtual_machine=self.vm, guest_type=GuestTypeChoices.CONTAINER
        )
        GuestProfile.objects.create(
            virtual_machine=make_vm("ct-103"), guest_type=GuestTypeChoices.CONTAINER
        )
        self.assertEqual(GuestProfile.objects.filter(vmid__isnull=True).count(), 2)

    def test_one_profile_per_guest(self):
        GuestProfile.objects.create(
            virtual_machine=self.vm, guest_type=GuestTypeChoices.CONTAINER
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            GuestProfile.objects.create(
                virtual_machine=self.vm, guest_type=GuestTypeChoices.VM
            )

    def test_node_is_protected(self):
        GuestProfile.objects.create(
            virtual_machine=self.vm, guest_type=GuestTypeChoices.CONTAINER, node=self.node
        )
        with self.assertRaises(ProtectedError), transaction.atomic():
            self.node.delete()

    def test_cascade_on_vm_delete(self):
        GuestProfile.objects.create(
            virtual_machine=self.vm, guest_type=GuestTypeChoices.CONTAINER
        )
        self.vm.delete()
        self.assertEqual(GuestProfile.objects.count(), 0)

    def test_container_rejects_kvm_intent(self):
        p = GuestProfile(
            virtual_machine=self.vm, guest_type=GuestTypeChoices.CONTAINER,
            bios=PveBiosChoices.OVMF, agent=True,
        )
        with self.assertRaises(ValidationError) as ctx:
            p.full_clean()
        self.assertIn("bios", ctx.exception.message_dict)
        self.assertIn("agent", ctx.exception.message_dict)

    def test_kvm_rejects_container_intent(self):
        p = GuestProfile(
            virtual_machine=self.vm, guest_type=GuestTypeChoices.VM,
            swap=512, features=[LxcFeatureChoices.NESTING], unprivileged=False,
        )
        with self.assertRaises(ValidationError) as ctx:
            p.full_clean()
        self.assertIn("swap", ctx.exception.message_dict)
        self.assertIn("features", ctx.exception.message_dict)

    def test_matching_intent_validates(self):
        GuestProfile(
            virtual_machine=self.vm, guest_type=GuestTypeChoices.CONTAINER,
            swap=512, features=[LxcFeatureChoices.NESTING], ostemplate="local:vztmpl/deb.tar.zst",
        ).full_clean()
        GuestProfile(
            virtual_machine=make_vm("kvm-1"), guest_type=GuestTypeChoices.VM,
            bios=PveBiosChoices.OVMF, cpu_type="host", agent=True, unprivileged=False,
        ).full_clean()

    def test_sandbox_of_self_rejected(self):
        p = GuestProfile(
            virtual_machine=self.vm, guest_type=GuestTypeChoices.CONTAINER, sandbox_of=self.vm
        )
        with self.assertRaises(ValidationError) as ctx:
            p.full_clean()
        self.assertIn("sandbox_of", ctx.exception.message_dict)

    def test_sandbox_of_other_ok(self):
        prod = make_vm("prod-thing")
        p = GuestProfile(
            virtual_machine=self.vm, guest_type=GuestTypeChoices.CONTAINER, sandbox_of=prod
        )
        p.full_clean()
        p.save()
        self.assertEqual(prod.sandbox_guests.count(), 1)

    def test_sandbox_source_delete_nulls_the_link(self):
        prod = make_vm("prod-thing")
        p = GuestProfile.objects.create(
            virtual_machine=self.vm, guest_type=GuestTypeChoices.CONTAINER, sandbox_of=prod
        )
        prod.delete()
        p.refresh_from_db()
        self.assertIsNone(p.sandbox_of)

    def test_no_secret_value_fields(self):
        """Policy: the model may reference a secret, never hold one."""
        names = {f.name for f in GuestProfile._meta.get_fields() if hasattr(f, "name")}
        for banned in ("password", "root_password", "secret", "token", "api_key"):
            self.assertNotIn(banned, names)


class GuestInterfaceConfigModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.vm = make_vm("ct-201")
        cls.iface = VMInterface.objects.create(virtual_machine=cls.vm, name="eth0")

    def test_create_str_and_url(self):
        c = GuestInterfaceConfig.objects.create(
            interface=self.iface, bridge="vmbr0", gateway="192.0.2.1"
        )
        self.assertEqual(str(c), f"{self.iface}: vmbr0")
        self.assertIn("/plugins/guests/interface-configs/", c.get_absolute_url())

    def test_str_without_bridge(self):
        c = GuestInterfaceConfig.objects.create(interface=self.iface)
        self.assertEqual(str(c), f"{self.iface}: no bridge")

    def test_one_config_per_interface(self):
        GuestInterfaceConfig.objects.create(interface=self.iface, bridge="vmbr0")
        with self.assertRaises(IntegrityError), transaction.atomic():
            GuestInterfaceConfig.objects.create(interface=self.iface, bridge="vmbr1")

    def test_gateway_must_be_an_address(self):
        c = GuestInterfaceConfig(interface=self.iface, gateway="not-an-ip")
        with self.assertRaises(ValidationError):
            c.full_clean()

    def test_cascade_on_interface_delete(self):
        GuestInterfaceConfig.objects.create(interface=self.iface, bridge="vmbr0")
        self.iface.delete()
        self.assertEqual(GuestInterfaceConfig.objects.count(), 0)
