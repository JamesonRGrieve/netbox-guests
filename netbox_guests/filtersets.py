# SPDX-License-Identifier: AGPL-3.0-or-later
import django_filters
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet
from dcim.models import Device
from virtualization.models import VMInterface, VirtualMachine
from .choices import (
    BackupModeChoices, DeviceKindChoices, GuestTypeChoices, PveBiosChoices,
)
from .models import (
    BackupJob, GuestDevice, GuestInterfaceConfig, GuestMount, GuestProfile,
)

# Explicit FK filters: django-filter does NOT derive `<fk>_id` from a bare FK in Meta.fields.
# NetBox convention is `<fk>_id` (by PK) + `<fk>` (by natural key/name).


class GuestMountFilterSet(NetBoxModelFilterSet):
    virtual_machine_id = django_filters.ModelMultipleChoiceFilter(
        field_name="virtual_machine", queryset=VirtualMachine.objects.all(),
        label="Virtual machine (ID)",
    )
    virtual_machine = django_filters.ModelMultipleChoiceFilter(
        field_name="virtual_machine__name", to_field_name="name",
        queryset=VirtualMachine.objects.all(), label="Virtual machine (name)",
    )

    class Meta:
        model = GuestMount
        fields = ["id", "mp", "volume", "path", "read_only", "backup"]

    def search(self, queryset, name, value):
        return queryset.filter(Q(volume__icontains=value) | Q(path__icontains=value))


class GuestDeviceFilterSet(NetBoxModelFilterSet):
    virtual_machine_id = django_filters.ModelMultipleChoiceFilter(
        field_name="virtual_machine", queryset=VirtualMachine.objects.all(),
        label="Virtual machine (ID)",
    )
    virtual_machine = django_filters.ModelMultipleChoiceFilter(
        field_name="virtual_machine__name", to_field_name="name",
        queryset=VirtualMachine.objects.all(), label="Virtual machine (name)",
    )
    kind = django_filters.MultipleChoiceFilter(choices=DeviceKindChoices)

    class Meta:
        model = GuestDevice
        fields = ["id", "kind", "selector", "index", "mode", "gid"]

    def search(self, queryset, name, value):
        return queryset.filter(Q(selector__icontains=value) | Q(description__icontains=value))


class GuestProfileFilterSet(NetBoxModelFilterSet):
    virtual_machine_id = django_filters.ModelMultipleChoiceFilter(
        field_name="virtual_machine", queryset=VirtualMachine.objects.all(),
        label="Virtual machine (ID)",
    )
    virtual_machine = django_filters.ModelMultipleChoiceFilter(
        field_name="virtual_machine__name", to_field_name="name",
        queryset=VirtualMachine.objects.all(), label="Virtual machine (name)",
    )
    node_id = django_filters.ModelMultipleChoiceFilter(
        field_name="node", queryset=Device.objects.all(), label="PVE node (ID)",
    )
    node = django_filters.ModelMultipleChoiceFilter(
        field_name="node__name", to_field_name="name",
        queryset=Device.objects.all(), label="PVE node (name)",
    )
    sandbox_of_id = django_filters.ModelMultipleChoiceFilter(
        field_name="sandbox_of", queryset=VirtualMachine.objects.all(),
        label="Sandbox of (ID)",
    )
    backup_job_id = django_filters.ModelMultipleChoiceFilter(
        field_name="backup_job", queryset=BackupJob.objects.all(), label="Backup job (ID)",
    )
    guest_type = django_filters.MultipleChoiceFilter(choices=GuestTypeChoices)
    bios = django_filters.MultipleChoiceFilter(choices=PveBiosChoices)

    class Meta:
        model = GuestProfile
        fields = [
            "id", "vmid", "pool", "storage", "onboot", "start", "protection", "bao_secret_path",
            "has_admin_password", "has_admin_token", "has_db_password", "has_secret_key",
            "swap", "unprivileged", "ostemplate", "template", "image", "iso", "cpu_type",
            "sockets", "numa", "agent", "cloud_init",
        ]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(virtual_machine__name__icontains=value) | Q(storage__icontains=value)
            | Q(ostemplate__icontains=value) | Q(template__icontains=value)
        )


class BackupJobFilterSet(NetBoxModelFilterSet):
    node_id = django_filters.ModelMultipleChoiceFilter(
        field_name="node", queryset=Device.objects.all(), label="PVE node (ID)",
    )
    node = django_filters.ModelMultipleChoiceFilter(
        field_name="node__name", to_field_name="name",
        queryset=Device.objects.all(), label="PVE node (name)",
    )
    mode = django_filters.MultipleChoiceFilter(choices=BackupModeChoices)

    class Meta:
        model = BackupJob
        fields = ("id", "job_id", "storage", "schedule", "enabled", "repeat_missed")

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(job_id__icontains=value) | Q(storage__icontains=value)
            | Q(description__icontains=value)
        )


class GuestInterfaceConfigFilterSet(NetBoxModelFilterSet):
    interface_id = django_filters.ModelMultipleChoiceFilter(
        field_name="interface", queryset=VMInterface.objects.all(), label="Interface (ID)",
    )
    virtual_machine_id = django_filters.ModelMultipleChoiceFilter(
        field_name="interface__virtual_machine", queryset=VirtualMachine.objects.all(),
        label="Virtual machine (ID)",
    )

    class Meta:
        model = GuestInterfaceConfig
        fields = ["id", "bridge", "gateway"]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(bridge__icontains=value) | Q(interface__virtual_machine__name__icontains=value)
        )
