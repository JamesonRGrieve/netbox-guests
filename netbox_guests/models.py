# SPDX-License-Identifier: AGPL-3.0-or-later
"""The guest layer is modeled on core ``virtualization.virtual-machine`` (LXC + KVM both,
distinguished by the ``guest_type`` custom field), with native ``VMInterface``/IPAM for the
network intent and typed **custom fields** for the PVE scalars (see :mod:`.customfields`).

The only relational model this plugin owns is :class:`GuestMount` -- the one repeating PVE
structure (``mp0..N``) that does not fit a scalar custom field. Everything else PVE-specific is
a custom field installed by the data migration.
"""
from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel

from .choices import DeviceKindChoices


class GuestMount(NetBoxModel):
    """A Proxmox mount point (``mpN``) on a guest: an in-guest path backed by a PVE volume or a
    host directory. Repeating per guest, so it is a child row rather than a custom field. The
    host-side existence of the backing volume/dir is owned by Ansible/host bootstrap, not here."""

    virtual_machine = models.ForeignKey(
        "virtualization.VirtualMachine", on_delete=models.CASCADE, related_name="guest_mounts"
    )
    mp = models.PositiveSmallIntegerField(help_text="Mount index N in the PVE mpN key.")
    volume = models.CharField(
        max_length=255,
        help_text="PVE volume or host path (e.g. 'local-zfs:subvol-…' or '/host/dir').",
    )
    path = models.CharField(max_length=255, help_text="In-guest mount path (the mp= target).")
    read_only = models.BooleanField(default=False, help_text="Mount read-only (ro=1).")

    class Meta:
        ordering = ["virtual_machine", "mp"]
        verbose_name = "Guest Mount"
        constraints = [
            models.UniqueConstraint(
                fields=["virtual_machine", "mp"],
                name="netbox_guests_guestmount_unique_vm_mp",
            ),
        ]

    def __str__(self):
        return f"{self.virtual_machine}: mp{self.mp} → {self.path}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_guests:guestmount", args=[self.pk])


class GuestDevice(NetBoxModel):
    """A host device passed through to a guest (PVE ``devN`` or the raw
    ``lxc.cgroup2.devices.allow`` + ``lxc.mount.entry`` pair). Repeating per guest, so it is a
    child row rather than a custom field — the sibling of :class:`GuestMount` for devices. This
    is the declared **intent**; the host-side existence of the device node (driver install, the
    ``/dev/nvidia*`` nodes, USB enumeration) is owned by host bootstrap, not here.

    A GPU service (ollama / vllm / comfyui) declares one row per ``/dev/nvidiaN`` plus the control
    nodes; a USB bridge (e.g. OctoPrint) declares the bus path or vendor:product device. The
    ``cgroup_allow`` / ``mount_entry`` fields carry the exact raw-LXC lines for the fallback path
    when a native ``devN`` param cannot express the passthrough."""

    virtual_machine = models.ForeignKey(
        "virtualization.VirtualMachine", on_delete=models.CASCADE, related_name="devices"
    )
    kind = models.CharField(
        max_length=16, choices=DeviceKindChoices,
        help_text="Device class: gpu / usb / tty / pci / other.",
    )
    selector = models.CharField(
        max_length=255,
        help_text=(
            "Host device selector: PCI addr (0000:07:00.0), USB vendor:product (2341:0043) or "
            "bus path (1-1.2), or a /dev/… / /dev/disk/by-id/… path."
        ),
    )
    index = models.PositiveSmallIntegerField(
        default=0, help_text="Ordering index (dev0/dev1…); distinguishes multiple GPUs on one guest."
    )
    cgroup_allow = models.CharField(
        max_length=255, blank=True,
        help_text="Raw-mode lxc.cgroup2.devices.allow value (e.g. 'c 195:* rwm' for nvidia).",
    )
    mount_entry = models.CharField(
        max_length=255, blank=True,
        help_text="Raw-mode lxc.mount.entry line for the device node.",
    )
    mode = models.CharField(
        max_length=16, blank=True, help_text="Optional device node permission bits (e.g. 0660)."
    )
    gid = models.PositiveIntegerField(
        null=True, blank=True, help_text="Optional group id owning the in-guest device node."
    )
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["virtual_machine", "kind", "index", "selector"]
        verbose_name = "Guest Device"
        constraints = [
            models.UniqueConstraint(
                fields=["virtual_machine", "kind", "selector", "index"],
                name="netbox_guests_guestdevice_unique_vm_kind_selector_index",
            ),
        ]

    def __str__(self):
        return f"{self.virtual_machine}: {self.kind}/{self.selector}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_guests:guestdevice", args=[self.pk])

    def get_kind_color(self):
        return DeviceKindChoices.colors.get(self.kind)
