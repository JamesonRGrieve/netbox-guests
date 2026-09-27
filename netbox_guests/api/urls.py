# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.routers import NetBoxRouter
from . import views

app_name = "netbox_guests"

router = NetBoxRouter()
router.register("mounts", views.GuestMountViewSet)
router.register("devices", views.GuestDeviceViewSet)
router.register("profiles", views.GuestProfileViewSet)
router.register("interface-configs", views.GuestInterfaceConfigViewSet)

urlpatterns = router.urls
