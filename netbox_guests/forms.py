# SPDX-License-Identifier: AGPL-3.0-or-later
from django import forms
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import (
    DynamicModelChoiceField, DynamicModelMultipleChoiceField, TagFilterField,
)
from utilities.forms.rendering import FieldSet
from virtualization.models import VirtualMachine
from .models import GuestMount


class GuestMountForm(NetBoxModelForm):
    virtual_machine = DynamicModelChoiceField(queryset=VirtualMachine.objects.all())

    fieldsets = (FieldSet("virtual_machine", "mp", "volume", "path", "read_only", name="Mount"),)

    class Meta:
        model = GuestMount
        fields = ["virtual_machine", "mp", "volume", "path", "read_only", "tags"]


class GuestMountFilterForm(NetBoxModelFilterSetForm):
    model = GuestMount
    virtual_machine_id = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(), required=False, label="Virtual machine"
    )
    read_only = forms.NullBooleanField(required=False)
    tag = TagFilterField(GuestMount)
