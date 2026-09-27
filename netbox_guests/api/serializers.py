# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers
from dcim.api.serializers import DeviceSerializer
from virtualization.api.serializers import (
    VMInterfaceSerializer, VirtualMachineSerializer,
)
from ..models import (
    GuestDevice, GuestInterfaceConfig, GuestMount, GuestProfile,
)


class GuestMountSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_guests-api:guestmount-detail")
    virtual_machine = VirtualMachineSerializer(nested=True)

    class Meta:
        model = GuestMount
        fields = [
            "id", "url", "display", "virtual_machine", "mp", "volume", "path", "read_only", "backup",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "virtual_machine", "mp", "path"]


class GuestDeviceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_guests-api:guestdevice-detail")
    virtual_machine = VirtualMachineSerializer(nested=True)

    class Meta:
        model = GuestDevice
        fields = [
            "id", "url", "display", "virtual_machine", "kind", "selector", "index",
            "cgroup_allow", "mount_entry", "mode", "gid", "description",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "virtual_machine", "kind", "selector", "index"]


class GuestProfileSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_guests-api:guestprofile-detail")
    virtual_machine = VirtualMachineSerializer(nested=True)
    node = DeviceSerializer(nested=True, required=False, allow_null=True)
    sandbox_of = VirtualMachineSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = GuestProfile
        fields = [
            "id", "url", "display", "virtual_machine", "guest_type", "vmid", "node", "pool",
            "storage", "onboot", "start", "sandbox_of", "description_template",
            "bao_secret_path", "has_admin_password", "has_admin_token", "has_db_password",
            "has_secret_key", "swap", "unprivileged", "features", "ostemplate", "template",
            "image", "iso", "bios", "cpu_type", "sockets", "numa", "agent", "cloud_init",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "virtual_machine", "guest_type", "vmid"]


class GuestInterfaceConfigSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_guests-api:guestinterfaceconfig-detail")
    interface = VMInterfaceSerializer(nested=True)

    class Meta:
        model = GuestInterfaceConfig
        fields = [
            "id", "url", "display", "interface", "bridge", "gateway",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "interface", "bridge", "gateway"]
