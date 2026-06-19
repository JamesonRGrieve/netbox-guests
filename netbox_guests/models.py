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
