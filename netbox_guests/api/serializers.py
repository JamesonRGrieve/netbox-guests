# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers
from virtualization.api.serializers import VirtualMachineSerializer
from ..models import GuestMount


class GuestMountSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_guests-api:guestmount-detail")
    virtual_machine = VirtualMachineSerializer(nested=True)

    class Meta:
        model = GuestMount
        fields = [
            "id", "url", "display", "virtual_machine", "mp", "volume", "path", "read_only",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "virtual_machine", "mp", "path"]
