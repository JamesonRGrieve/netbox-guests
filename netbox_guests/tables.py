# SPDX-License-Identifier: AGPL-3.0-or-later
import django_tables2 as tables
from netbox.tables import NetBoxTable, columns
from .models import GuestMount


class GuestMountTable(NetBoxTable):
    virtual_machine = tables.Column(linkify=True)
    path = tables.Column(linkify=True)
    read_only = columns.BooleanColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_guests:guestmount_list")

    class Meta(NetBoxTable.Meta):
        model = GuestMount
        fields = ("pk", "id", "virtual_machine", "mp", "volume", "path", "read_only", "tags", "created", "last_updated")
        default_columns = ("virtual_machine", "mp", "volume", "path", "read_only")
