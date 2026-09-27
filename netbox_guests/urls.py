# SPDX-License-Identifier: AGPL-3.0-or-later
from django.urls import path
from netbox.views.generic import ObjectChangeLogView, ObjectJournalView
from . import models, views

urlpatterns = [
    path("mounts/", views.GuestMountListView.as_view(), name="guestmount_list"),
    path("mounts/add/", views.GuestMountEditView.as_view(), name="guestmount_add"),
    path("mounts/delete/", views.GuestMountBulkDeleteView.as_view(), name="guestmount_bulk_delete"),
    path("mounts/<int:pk>/", views.GuestMountView.as_view(), name="guestmount"),
    path("mounts/<int:pk>/edit/", views.GuestMountEditView.as_view(), name="guestmount_edit"),
    path("mounts/<int:pk>/delete/", views.GuestMountDeleteView.as_view(), name="guestmount_delete"),
    path("mounts/<int:pk>/changelog/", ObjectChangeLogView.as_view(), name="guestmount_changelog", kwargs={"model": models.GuestMount}),
    path("mounts/<int:pk>/journal/", ObjectJournalView.as_view(), name="guestmount_journal", kwargs={"model": models.GuestMount}),
    path("devices/", views.GuestDeviceListView.as_view(), name="guestdevice_list"),
    path("devices/add/", views.GuestDeviceEditView.as_view(), name="guestdevice_add"),
    path("devices/delete/", views.GuestDeviceBulkDeleteView.as_view(), name="guestdevice_bulk_delete"),
    path("devices/<int:pk>/", views.GuestDeviceView.as_view(), name="guestdevice"),
    path("devices/<int:pk>/edit/", views.GuestDeviceEditView.as_view(), name="guestdevice_edit"),
    path("devices/<int:pk>/delete/", views.GuestDeviceDeleteView.as_view(), name="guestdevice_delete"),
    path("devices/<int:pk>/changelog/", ObjectChangeLogView.as_view(), name="guestdevice_changelog", kwargs={"model": models.GuestDevice}),
    path("devices/<int:pk>/journal/", ObjectJournalView.as_view(), name="guestdevice_journal", kwargs={"model": models.GuestDevice}),
    path("profiles/", views.GuestProfileListView.as_view(), name="guestprofile_list"),
    path("profiles/add/", views.GuestProfileEditView.as_view(), name="guestprofile_add"),
    path("profiles/delete/", views.GuestProfileBulkDeleteView.as_view(), name="guestprofile_bulk_delete"),
    path("profiles/<int:pk>/", views.GuestProfileView.as_view(), name="guestprofile"),
    path("profiles/<int:pk>/edit/", views.GuestProfileEditView.as_view(), name="guestprofile_edit"),
    path("profiles/<int:pk>/delete/", views.GuestProfileDeleteView.as_view(), name="guestprofile_delete"),
    path("profiles/<int:pk>/changelog/", ObjectChangeLogView.as_view(), name="guestprofile_changelog", kwargs={"model": models.GuestProfile}),
    path("profiles/<int:pk>/journal/", ObjectJournalView.as_view(), name="guestprofile_journal", kwargs={"model": models.GuestProfile}),
    path("interface-configs/", views.GuestInterfaceConfigListView.as_view(), name="guestinterfaceconfig_list"),
    path("interface-configs/add/", views.GuestInterfaceConfigEditView.as_view(), name="guestinterfaceconfig_add"),
    path("interface-configs/delete/", views.GuestInterfaceConfigBulkDeleteView.as_view(), name="guestinterfaceconfig_bulk_delete"),
    path("interface-configs/<int:pk>/", views.GuestInterfaceConfigView.as_view(), name="guestinterfaceconfig"),
    path("interface-configs/<int:pk>/edit/", views.GuestInterfaceConfigEditView.as_view(), name="guestinterfaceconfig_edit"),
    path("interface-configs/<int:pk>/delete/", views.GuestInterfaceConfigDeleteView.as_view(), name="guestinterfaceconfig_delete"),
    path("interface-configs/<int:pk>/changelog/", ObjectChangeLogView.as_view(), name="guestinterfaceconfig_changelog", kwargs={"model": models.GuestInterfaceConfig}),
    path("interface-configs/<int:pk>/journal/", ObjectJournalView.as_view(), name="guestinterfaceconfig_journal", kwargs={"model": models.GuestInterfaceConfig}),
]
