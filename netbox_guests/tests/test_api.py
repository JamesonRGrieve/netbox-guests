# SPDX-License-Identifier: AGPL-3.0-or-later
"""REST API CRUD tests (real DB + real API client, no mocks). Composes the explicit CRUD mixins
(no GraphQL type shipped). The (vm, mp) unique constraint means each row needs a distinct mp."""
from utilities.testing import APIViewTestCases
from netbox_guests.models import GuestMount
from .utils import make_vm


class _CRUD(
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
):
    pass


class GuestMountAPITest(_CRUD):
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
            {"virtual_machine": vm.pk, "mp": 11, "volume": "local:11", "path": "/y", "read_only": True},
            {"virtual_machine": vm.pk, "mp": 12, "volume": "local:12", "path": "/z"},
        ]
