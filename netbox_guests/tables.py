# SPDX-License-Identifier: AGPL-3.0-or-later
import django_tables2 as tables
from netbox.tables import NetBoxTable, columns
from .models import GuestDevice, GuestMount


class GuestMountTable(NetBoxTable):
    virtual_machine = tables.Column(linkify=True)
    path = tables.Column(linkify=True)
    read_only = columns.BooleanColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_guests:guestmount_list")

    class Meta(NetBoxTable.Meta):
        model = GuestMount
        fields = ("pk", "id", "virtual_machine", "mp", "volume", "path", "read_only", "tags", "created", "last_updated")
        default_columns = ("virtual_machine", "mp", "volume", "path", "read_only")


class GuestDeviceTable(NetBoxTable):
    virtual_machine = tables.Column(linkify=True)
    kind = columns.ChoiceFieldColumn()
    selector = tables.Column(linkify=True)
    tags = columns.TagColumn(url_name="plugins:netbox_guests:guestdevice_list")

    class Meta(NetBoxTable.Meta):
        model = GuestDevice
        fields = (
            "pk", "id", "virtual_machine", "kind", "selector", "index", "cgroup_allow",
            "mount_entry", "mode", "gid", "description", "tags", "created", "last_updated",
        )
        default_columns = ("virtual_machine", "kind", "selector", "index", "cgroup_allow")
