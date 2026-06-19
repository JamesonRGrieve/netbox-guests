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
]
