# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.viewsets import NetBoxModelViewSet
from .. import filtersets
from ..models import GuestDevice, GuestMount
from .serializers import GuestDeviceSerializer, GuestMountSerializer


class GuestMountViewSet(NetBoxModelViewSet):
    queryset = GuestMount.objects.prefetch_related("virtual_machine", "tags")
    serializer_class = GuestMountSerializer
    filterset_class = filtersets.GuestMountFilterSet


class GuestDeviceViewSet(NetBoxModelViewSet):
    queryset = GuestDevice.objects.prefetch_related("virtual_machine", "tags")
    serializer_class = GuestDeviceSerializer
    filterset_class = filtersets.GuestDeviceFilterSet
