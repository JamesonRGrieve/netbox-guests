# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.views import generic
from . import filtersets, forms, models, tables


class GuestMountView(generic.ObjectView):
    queryset = models.GuestMount.objects.all()


class GuestMountListView(generic.ObjectListView):
    queryset = models.GuestMount.objects.all()
    table = tables.GuestMountTable
    filterset = filtersets.GuestMountFilterSet
    filterset_form = forms.GuestMountFilterForm


class GuestMountEditView(generic.ObjectEditView):
    queryset = models.GuestMount.objects.all()
    form = forms.GuestMountForm


class GuestMountDeleteView(generic.ObjectDeleteView):
    queryset = models.GuestMount.objects.all()


class GuestMountBulkDeleteView(generic.BulkDeleteView):
    queryset = models.GuestMount.objects.all()
    table = tables.GuestMountTable
