# SPDX-License-Identifier: AGPL-3.0-or-later
import django_filters
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet
from virtualization.models import VirtualMachine
from .models import GuestMount

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
        fields = ["id", "mp", "volume", "path", "read_only"]

    def search(self, queryset, name, value):
        return queryset.filter(Q(volume__icontains=value) | Q(path__icontains=value))
