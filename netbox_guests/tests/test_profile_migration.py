# SPDX-License-Identifier: AGPL-3.0-or-later
"""The 0006 data migration, exercised against a real DB (no mocks).

Its forward/backward functions take Django's ``apps`` registry, so they are invoked here with the
live registry — the same code path the migration runs, not a reimplementation. The module name
starts with a digit, so it is loaded via :mod:`importlib`.

What is asserted is what makes the migration safe to run on prod: values carried across exactly, a
guest with nothing recorded getting no row at all, idempotency on re-run, a dangling object
reference dropped rather than guessed, and a faithful round trip back into ``custom_field_data``.
"""
from importlib import import_module

from django.apps import apps as global_apps
from django.test import TestCase
from virtualization.models import VMInterface
from netbox_guests.models import GuestInterfaceConfig, GuestProfile
from .test_profile import make_device
from .utils import make_vm

_mig = import_module("netbox_guests.migrations.0006_custom_fields_to_profile")
forward = _mig.forward
backward = _mig.backward


class ProfileMigrationTest(TestCase):
    def _run_forward(self):
        forward(global_apps, None)

    def test_scalars_and_booleans_carried_across(self):
        vm = make_vm("ct-301")
        vm.custom_field_data = {
            "guest_type": "container", "vmid": 301, "storage": "local-zfs", "pool": "prod",
            "onboot": True, "swap": 512, "unprivileged": True,
            "features": ["nesting", "keyctl"], "ostemplate": "local:vztmpl/deb.tar.zst",
            "bao_secret_path": "prod/zephyrex/ct/ct-301", "has_db_password": True,
        }
        vm.save()
        self._run_forward()
        p = GuestProfile.objects.get(virtual_machine=vm)
        self.assertEqual(p.guest_type, "container")
        self.assertEqual(p.vmid, 301)
        self.assertEqual(p.storage, "local-zfs")
        self.assertEqual(p.pool, "prod")
        self.assertTrue(p.onboot)
        self.assertEqual(p.swap, 512)
        self.assertEqual(p.features, ["nesting", "keyctl"])
        self.assertEqual(p.bao_secret_path, "prod/zephyrex/ct/ct-301")
        self.assertTrue(p.has_db_password)
        self.assertFalse(p.has_admin_password, "an unset flag must stay false, not become true")

    def test_object_reference_becomes_a_real_fk(self):
        node = make_device("core")
        prod = make_vm("prod-src")
        vm = make_vm("ct-302")
        vm.custom_field_data = {"guest_type": "container", "node": node.pk, "sandbox_of": prod.pk}
        vm.save()
        self._run_forward()
        p = GuestProfile.objects.get(virtual_machine=vm)
        self.assertEqual(p.node_id, node.pk)
        self.assertEqual(p.sandbox_of_id, prod.pk)

    def test_dangling_object_reference_is_dropped_not_guessed(self):
        vm = make_vm("ct-303")
        vm.custom_field_data = {"guest_type": "container", "node": 10_000_000}
        vm.save()
        self._run_forward()
        p = GuestProfile.objects.get(virtual_machine=vm)
        self.assertIsNone(p.node_id)

    def test_self_sandbox_reference_is_dropped(self):
        vm = make_vm("ct-304")
        vm.custom_field_data = {"guest_type": "container", "sandbox_of": vm.pk}
        vm.save()
        self._run_forward()
        self.assertIsNone(GuestProfile.objects.get(virtual_machine=vm).sandbox_of_id)

    def test_guest_with_nothing_recorded_gets_no_profile(self):
        make_vm("ct-305")
        self._run_forward()
        self.assertFalse(GuestProfile.objects.filter(virtual_machine__name="ct-305").exists())

    def test_empty_values_count_as_absent(self):
        vm = make_vm("ct-306")
        vm.custom_field_data = {"guest_type": "", "storage": "", "features": [], "vmid": None}
        vm.save()
        self._run_forward()
        self.assertFalse(GuestProfile.objects.filter(virtual_machine=vm).exists())

    def test_missing_guest_type_defaults_to_container(self):
        vm = make_vm("ct-307")
        vm.custom_field_data = {"vmid": 307}
        vm.save()
        self._run_forward()
        self.assertEqual(GuestProfile.objects.get(virtual_machine=vm).guest_type, "container")

    def test_uncoercible_value_is_left_behind_not_guessed(self):
        vm = make_vm("ct-308")
        vm.custom_field_data = {"guest_type": "container", "vmid": "not-a-number", "storage": "z"}
        vm.save()
        self._run_forward()
        p = GuestProfile.objects.get(virtual_machine=vm)
        self.assertIsNone(p.vmid)
        self.assertEqual(p.storage, "z")

    def test_idempotent_on_rerun_and_does_not_clobber_edits(self):
        vm = make_vm("ct-309")
        vm.custom_field_data = {"guest_type": "container", "storage": "old"}
        vm.save()
        self._run_forward()
        p = GuestProfile.objects.get(virtual_machine=vm)
        p.storage = "edited-since"
        p.save()
        self._run_forward()
        self.assertEqual(GuestProfile.objects.filter(virtual_machine=vm).count(), 1)
        self.assertEqual(GuestProfile.objects.get(virtual_machine=vm).storage, "edited-since")

    def test_interface_bridge_and_gateway(self):
        vm = make_vm("ct-310")
        iface = VMInterface.objects.create(virtual_machine=vm, name="eth0")
        iface.custom_field_data = {"bridge": "vmbr0", "gateway": "192.0.2.1"}
        iface.save()
        self._run_forward()
        cfg = GuestInterfaceConfig.objects.get(interface=iface)
        self.assertEqual(cfg.bridge, "vmbr0")
        self.assertEqual(cfg.gateway, "192.0.2.1")

    def test_interface_gateway_with_mask_is_stripped(self):
        vm = make_vm("ct-311")
        iface = VMInterface.objects.create(virtual_machine=vm, name="eth0")
        iface.custom_field_data = {"gateway": "192.0.2.1/24"}
        iface.save()
        self._run_forward()
        self.assertEqual(GuestInterfaceConfig.objects.get(interface=iface).gateway, "192.0.2.1")

    def test_interface_with_nothing_recorded_gets_no_row(self):
        vm = make_vm("ct-312")
        VMInterface.objects.create(virtual_machine=vm, name="eth0")
        self._run_forward()
        self.assertEqual(GuestInterfaceConfig.objects.count(), 0)

    def test_backward_restores_the_custom_field_data(self):
        node = make_device("core")
        vm = make_vm("ct-313")
        original = {
            "guest_type": "container", "vmid": 313, "storage": "local-zfs",
            "onboot": True, "node": node.pk,
        }
        vm.custom_field_data = dict(original)
        vm.save()
        self._run_forward()
        # Simulate 0008 having cleared the custom fields before a rollback.
        vm.custom_field_data = {}
        vm.save()

        backward(global_apps, None)

        vm.refresh_from_db()
        for key, value in original.items():
            self.assertEqual(vm.custom_field_data.get(key), value, msg=key)
        self.assertEqual(GuestProfile.objects.count(), 0)

    def test_backward_round_trips_interface_config(self):
        vm = make_vm("ct-314")
        iface = VMInterface.objects.create(virtual_machine=vm, name="eth0")
        iface.custom_field_data = {"bridge": "vmbr0", "gateway": "192.0.2.1"}
        iface.save()
        self._run_forward()
        iface.custom_field_data = {}
        iface.save()

        backward(global_apps, None)

        iface.refresh_from_db()
        self.assertEqual(iface.custom_field_data.get("bridge"), "vmbr0")
        self.assertEqual(iface.custom_field_data.get("gateway"), "192.0.2.1")
        self.assertEqual(GuestInterfaceConfig.objects.count(), 0)
