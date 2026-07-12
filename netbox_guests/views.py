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


class GuestDeviceView(generic.ObjectView):
    queryset = models.GuestDevice.objects.all()


class GuestDeviceListView(generic.ObjectListView):
    queryset = models.GuestDevice.objects.all()
    table = tables.GuestDeviceTable
    filterset = filtersets.GuestDeviceFilterSet
    filterset_form = forms.GuestDeviceFilterForm


class GuestDeviceEditView(generic.ObjectEditView):
    queryset = models.GuestDevice.objects.all()
    form = forms.GuestDeviceForm


class GuestDeviceDeleteView(generic.ObjectDeleteView):
    queryset = models.GuestDevice.objects.all()


class GuestDeviceBulkDeleteView(generic.BulkDeleteView):
    queryset = models.GuestDevice.objects.all()
    table = tables.GuestDeviceTable
