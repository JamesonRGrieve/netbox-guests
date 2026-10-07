# SPDX-License-Identifier: AGPL-3.0-or-later
from django import forms
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import (
    DynamicModelChoiceField, DynamicModelMultipleChoiceField, TagFilterField,
)
from utilities.forms.rendering import FieldSet
from dcim.models import Device
from virtualization.models import VMInterface, VirtualMachine
from .choices import (
    BackupModeChoices, DeviceKindChoices, GuestTypeChoices, PveBiosChoices,
)
from .models import (
    BackupJob, GuestDevice, GuestInterfaceConfig, GuestMount, GuestProfile,
)


class GuestMountForm(NetBoxModelForm):
    virtual_machine = DynamicModelChoiceField(queryset=VirtualMachine.objects.all())

    fieldsets = (
        FieldSet("virtual_machine", "mp", "volume", "path", "read_only", "backup", name="Mount"),
    )

    class Meta:
        model = GuestMount
        fields = ["virtual_machine", "mp", "volume", "path", "read_only", "backup", "tags"]


class GuestMountFilterForm(NetBoxModelFilterSetForm):
    model = GuestMount
    virtual_machine_id = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(), required=False, label="Virtual machine"
    )
    read_only = forms.NullBooleanField(required=False)
    tag = TagFilterField(GuestMount)


class GuestDeviceForm(NetBoxModelForm):
    virtual_machine = DynamicModelChoiceField(queryset=VirtualMachine.objects.all())

    fieldsets = (
        FieldSet("virtual_machine", "kind", "selector", "index", "description", name="Device"),
        FieldSet("cgroup_allow", "mount_entry", "mode", "gid", name="Raw LXC (fallback)"),
    )

    class Meta:
        model = GuestDevice
        fields = [
            "virtual_machine", "kind", "selector", "index", "cgroup_allow", "mount_entry",
            "mode", "gid", "description", "tags",
        ]


class GuestDeviceFilterForm(NetBoxModelFilterSetForm):
    model = GuestDevice
    virtual_machine_id = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(), required=False, label="Virtual machine"
    )
    kind = forms.MultipleChoiceField(choices=DeviceKindChoices, required=False)
    tag = TagFilterField(GuestDevice)


class GuestProfileForm(NetBoxModelForm):
    virtual_machine = DynamicModelChoiceField(queryset=VirtualMachine.objects.all())
    node = DynamicModelChoiceField(queryset=Device.objects.all(), required=False)
    sandbox_of = DynamicModelChoiceField(queryset=VirtualMachine.objects.all(), required=False)
    backup_job = DynamicModelChoiceField(
        queryset=BackupJob.objects.all(), required=False, query_params={"node_id": "$node"}
    )

    fieldsets = (
        FieldSet("virtual_machine", "guest_type", "vmid", "node", "pool", "storage",
                 "onboot", "start", "protection", "backup_job", name="Guest"),
        FieldSet("swap", "unprivileged", "features", "ostemplate", name="Container (LXC)"),
        FieldSet("template", "image", "iso", "bios", "cpu_type", "sockets", "numa", "agent",
                 "cloud_init", name="Virtual machine (KVM)"),
        FieldSet("bao_secret_path", "has_admin_password", "has_admin_token", "has_db_password",
                 "has_secret_key", name="Credentials (references only)"),
        FieldSet("sandbox_of", "description_template", name="Provenance"),
    )

    class Meta:
        model = GuestProfile
        fields = [
            "virtual_machine", "guest_type", "vmid", "node", "pool", "storage", "onboot",
            "start", "protection", "backup_job", "swap", "unprivileged", "features", "ostemplate",
            "template", "image", "iso", "bios", "cpu_type", "sockets", "numa", "agent",
            "cloud_init", "bao_secret_path", "has_admin_password", "has_admin_token", "has_db_password",
            "has_secret_key", "sandbox_of", "description_template", "tags",
        ]


class GuestProfileFilterForm(NetBoxModelFilterSetForm):
    model = GuestProfile
    virtual_machine_id = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(), required=False, label="Virtual machine"
    )
    node_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(), required=False, label="PVE node"
    )
    backup_job_id = DynamicModelMultipleChoiceField(
        queryset=BackupJob.objects.all(), required=False, label="Backup job"
    )
    guest_type = forms.MultipleChoiceField(choices=GuestTypeChoices, required=False)
    bios = forms.MultipleChoiceField(choices=PveBiosChoices, required=False)
    onboot = forms.NullBooleanField(required=False)
    protection = forms.NullBooleanField(required=False)
    unprivileged = forms.NullBooleanField(required=False)
    tag = TagFilterField(GuestProfile)


class BackupJobForm(NetBoxModelForm):
    node = DynamicModelChoiceField(queryset=Device.objects.all())

    fieldsets = (
        FieldSet("node", "job_id", "storage", "schedule", "mode", "enabled", "description",
                 name="Backup job"),
        FieldSet("notes_template", "repeat_missed", "notification_mode", name="Options"),
    )

    class Meta:
        model = BackupJob
        fields = (
            "node", "job_id", "storage", "schedule", "mode", "enabled", "notes_template",
            "repeat_missed", "notification_mode", "description", "tags",
        )


class BackupJobFilterForm(NetBoxModelFilterSetForm):
    model = BackupJob
    node_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(), required=False, label="PVE node"
    )
    mode = forms.MultipleChoiceField(choices=BackupModeChoices, required=False)
    enabled = forms.NullBooleanField(required=False)
    tag = TagFilterField(BackupJob)


class GuestInterfaceConfigForm(NetBoxModelForm):
    interface = DynamicModelChoiceField(queryset=VMInterface.objects.all())

    fieldsets = (FieldSet("interface", "bridge", "gateway", name="Guest NIC"),)

    class Meta:
        model = GuestInterfaceConfig
        fields = ["interface", "bridge", "gateway", "tags"]


class GuestInterfaceConfigFilterForm(NetBoxModelFilterSetForm):
    model = GuestInterfaceConfig
    virtual_machine_id = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(), required=False, label="Virtual machine"
    )
    tag = TagFilterField(GuestInterfaceConfig)
