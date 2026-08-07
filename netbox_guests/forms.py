# SPDX-License-Identifier: AGPL-3.0-or-later
from django import forms
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import (
    DynamicModelChoiceField, DynamicModelMultipleChoiceField, TagFilterField,
)
from utilities.forms.rendering import FieldSet
from virtualization.models import VirtualMachine
from .choices import DeviceKindChoices
from .models import GuestDevice, GuestMount


class GuestMountForm(NetBoxModelForm):
    virtual_machine = DynamicModelChoiceField(queryset=VirtualMachine.objects.all())

    fieldsets = (FieldSet("virtual_machine", "mp", "volume", "path", "read_only", "backup", name="Mount"),)

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
