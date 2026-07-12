# SPDX-License-Identifier: AGPL-3.0-or-later
"""Choice sets for the guest models. The only choice domain the plugin owns is the passthrough
device *kind* (see :class:`netbox_guests.models.GuestDevice`)."""
from utilities.choices import ChoiceSet


class DeviceKindChoices(ChoiceSet):
    """Kind of host device passed through to a guest. ``gpu`` (NVIDIA/AMD render+compute nodes),
    ``usb`` (a USB bus path or vendor:product device — e.g. an OctoPrint printer bridge), ``tty``
    (a serial/character device such as ``/dev/ttyUSB0``), ``pci`` (a raw PCI function), or
    ``other`` (anything else expressed purely via cgroup_allow + mount_entry)."""
    GPU = "gpu"
    USB = "usb"
    TTY = "tty"
    PCI = "pci"
    OTHER = "other"
    CHOICES = [
        (GPU, "GPU", "green"),
        (USB, "USB", "blue"),
        (TTY, "TTY / serial", "cyan"),
        (PCI, "PCI", "purple"),
        (OTHER, "Other", "gray"),
    ]
