# SPDX-License-Identifier: AGPL-3.0-or-later
"""PveStorage tests against a real DB (no mocks).

Covers the model's contract: a storage id is unique per node (not fleet-wide), the node and the
server address cannot be deleted out from under a storage, the PBS fingerprint is format-checked,
and the type is a real choice.
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import ProtectedError
from django.db.utils import IntegrityError
from django.test import TestCase
from ipam.models import IPAddress

from netbox_guests.choices import PveStorageTypeChoices
from netbox_guests.models import PveStorage

from .test_profile import make_device

FP = ":".join(["ab"] * 32)


def make_storage(node, server, storage_id="pbs", **kwargs):
    return PveStorage.objects.create(
        node=node, storage_id=storage_id, server=server, datastore="pbs", username="pve@pbs",
        bao_secret_path="prod/boden/infra/hq/pbs/pve", **kwargs,
    )


class PveStorageModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sandbox = make_device("sandbox")
        cls.core = make_device("core")
        cls.ip = IPAddress.objects.create(address="172.23.0.250/24")

    def test_create_defaults_str_and_url(self):
        s = make_storage(self.sandbox, self.ip)
        self.assertEqual(str(s), "sandbox: pbs")
        self.assertIn("/plugins/guests/storages/", s.get_absolute_url())
        self.assertEqual(s.type, PveStorageTypeChoices.PBS)
        self.assertEqual(s.port, 8007)
        self.assertEqual(s.content, "backup")
        self.assertTrue(s.enabled)
        self.assertEqual(s.fingerprint, "")

    def test_storage_id_unique_per_node_not_fleet_wide(self):
        make_storage(self.sandbox, self.ip)
        make_storage(self.core, self.ip)
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_storage(self.sandbox, self.ip)

    def test_node_cannot_be_deleted_under_its_storage(self):
        node = make_device("doomed")
        make_storage(node, self.ip)
        with self.assertRaises(ProtectedError):
            node.delete()

    def test_server_address_cannot_be_deleted_under_its_storage(self):
        ip = IPAddress.objects.create(address="172.23.0.251/24")
        make_storage(self.sandbox, ip, storage_id="pbs2")
        with self.assertRaises(ProtectedError):
            ip.delete()

    def test_fingerprint_must_be_32_hex_octets(self):
        for bad in ("ab:cd", FP + ":ef", FP.replace("ab", "zz", 1), FP.replace(":", "-")):
            s = PveStorage(node=self.sandbox, storage_id="x", server=self.ip, datastore="pbs",
                           username="pve@pbs", bao_secret_path="p", fingerprint=bad)
            with self.assertRaises(ValidationError, msg=bad):
                s.full_clean()
        PveStorage(node=self.sandbox, storage_id="x", server=self.ip, datastore="pbs",
                   username="pve@pbs", bao_secret_path="p", fingerprint=FP.upper()).full_clean()

    def test_blank_fingerprint_is_valid_until_the_server_exists(self):
        PveStorage(node=self.sandbox, storage_id="x", server=self.ip, datastore="pbs",
                   username="pve@pbs", bao_secret_path="p").full_clean()

    def test_type_choice_is_validated(self):
        s = PveStorage(node=self.sandbox, storage_id="x", server=self.ip, datastore="pbs",
                       username="pve@pbs", bao_secret_path="p", type="nfs")
        with self.assertRaises(ValidationError):
            s.full_clean()
