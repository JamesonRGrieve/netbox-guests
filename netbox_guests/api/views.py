# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.viewsets import NetBoxModelViewSet
from .. import filtersets
from ..models import (
    GuestDevice, GuestInterfaceConfig, GuestMount, GuestProfile,
)
from .serializers import (
    GuestDeviceSerializer, GuestInterfaceConfigSerializer, GuestMountSerializer,
    GuestProfileSerializer,
)


class GuestMountViewSet(NetBoxModelViewSet):
    queryset = GuestMount.objects.prefetch_related("virtual_machine", "tags")
    serializer_class = GuestMountSerializer
    filterset_class = filtersets.GuestMountFilterSet


class GuestDeviceViewSet(NetBoxModelViewSet):
    queryset = GuestDevice.objects.prefetch_related("virtual_machine", "tags")
    serializer_class = GuestDeviceSerializer
    filterset_class = filtersets.GuestDeviceFilterSet


class GuestProfileViewSet(NetBoxModelViewSet):
    queryset = GuestProfile.objects.prefetch_related(
        "virtual_machine", "node", "sandbox_of", "tags"
    )
    serializer_class = GuestProfileSerializer
    filterset_class = filtersets.GuestProfileFilterSet


class GuestInterfaceConfigViewSet(NetBoxModelViewSet):
    queryset = GuestInterfaceConfig.objects.prefetch_related("interface", "tags")
    serializer_class = GuestInterfaceConfigSerializer
    filterset_class = filtersets.GuestInterfaceConfigFilterSet
