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


class GuestProfileView(generic.ObjectView):
    queryset = models.GuestProfile.objects.all()


class GuestProfileListView(generic.ObjectListView):
    queryset = models.GuestProfile.objects.all()
    table = tables.GuestProfileTable
    filterset = filtersets.GuestProfileFilterSet
    filterset_form = forms.GuestProfileFilterForm


class GuestProfileEditView(generic.ObjectEditView):
    queryset = models.GuestProfile.objects.all()
    form = forms.GuestProfileForm


class GuestProfileDeleteView(generic.ObjectDeleteView):
    queryset = models.GuestProfile.objects.all()


class GuestProfileBulkDeleteView(generic.BulkDeleteView):
    queryset = models.GuestProfile.objects.all()
    table = tables.GuestProfileTable


class GuestInterfaceConfigView(generic.ObjectView):
    queryset = models.GuestInterfaceConfig.objects.all()


class GuestInterfaceConfigListView(generic.ObjectListView):
    queryset = models.GuestInterfaceConfig.objects.all()
    table = tables.GuestInterfaceConfigTable
    filterset = filtersets.GuestInterfaceConfigFilterSet
    filterset_form = forms.GuestInterfaceConfigFilterForm


class GuestInterfaceConfigEditView(generic.ObjectEditView):
    queryset = models.GuestInterfaceConfig.objects.all()
    form = forms.GuestInterfaceConfigForm


class GuestInterfaceConfigDeleteView(generic.ObjectDeleteView):
    queryset = models.GuestInterfaceConfig.objects.all()


class GuestInterfaceConfigBulkDeleteView(generic.BulkDeleteView):
    queryset = models.GuestInterfaceConfig.objects.all()
    table = tables.GuestInterfaceConfigTable
