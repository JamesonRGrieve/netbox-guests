# SPDX-License-Identifier: AGPL-3.0-or-later
import django_tables2 as tables
from netbox.tables import NetBoxTable, columns
from .models import (
    BackupJob, GuestDevice, GuestInterfaceConfig, GuestMount, GuestProfile,
)


class GuestMountTable(NetBoxTable):
    virtual_machine = tables.Column(linkify=True)
    path = tables.Column(linkify=True)
    read_only = columns.BooleanColumn()
    backup = columns.BooleanColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_guests:guestmount_list")

    class Meta(NetBoxTable.Meta):
        model = GuestMount
        fields = (
            "pk", "id", "virtual_machine", "mp", "volume", "path", "read_only", "backup", "tags",
            "created", "last_updated",
        )
        default_columns = ("virtual_machine", "mp", "volume", "path", "read_only", "backup")


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


class GuestProfileTable(NetBoxTable):
    virtual_machine = tables.Column(linkify=True)
    guest_type = columns.ChoiceFieldColumn()
    node = tables.Column(linkify=True)
    sandbox_of = tables.Column(linkify=True)
    backup_job = tables.Column(linkify=True)
    onboot = columns.BooleanColumn()
    start = columns.BooleanColumn()
    protection = columns.BooleanColumn()
    unprivileged = columns.BooleanColumn()
    numa = columns.BooleanColumn()
    agent = columns.BooleanColumn()
    cloud_init = columns.BooleanColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_guests:guestprofile_list")

    class Meta(NetBoxTable.Meta):
        model = GuestProfile
        fields = (
            "pk", "id", "virtual_machine", "guest_type", "vmid", "node", "pool", "storage",
            "onboot", "start", "protection", "sandbox_of", "backup_job", "swap", "unprivileged",
            "features",
            "ostemplate", "template", "image", "iso", "bios", "cpu_type", "sockets", "numa",
            "agent", "cloud_init", "bao_secret_path", "tags", "created", "last_updated",
        )
        default_columns = (
            "virtual_machine", "guest_type", "vmid", "node", "storage", "onboot", "unprivileged",
        )


class BackupJobTable(NetBoxTable):
    node = tables.Column(linkify=True)
    job_id = tables.Column(linkify=True)
    mode = columns.ChoiceFieldColumn()
    enabled = columns.BooleanColumn()
    repeat_missed = columns.BooleanColumn()
    notification_mode = columns.ChoiceFieldColumn()
    vmids = tables.Column(verbose_name="VMIDs", orderable=False)
    tags = columns.TagColumn(url_name="plugins:netbox_guests:backupjob_list")

    class Meta(NetBoxTable.Meta):
        model = BackupJob
        fields = (
            "pk", "id", "node", "job_id", "storage", "schedule", "mode", "enabled",
            "notes_template", "repeat_missed", "notification_mode", "vmids",
            "description", "tags", "created", "last_updated",
        )
        default_columns = ("node", "job_id", "storage", "schedule", "mode", "enabled", "vmids")

    def render_vmids(self, value):
        return ", ".join(str(v) for v in value) or "—"


class GuestInterfaceConfigTable(NetBoxTable):
    interface = tables.Column(linkify=True)
    tags = columns.TagColumn(url_name="plugins:netbox_guests:guestinterfaceconfig_list")

    class Meta(NetBoxTable.Meta):
        model = GuestInterfaceConfig
        fields = ("pk", "id", "interface", "bridge", "gateway", "tags", "created", "last_updated")
        default_columns = ("interface", "bridge", "gateway")
