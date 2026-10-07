# SPDX-License-Identifier: AGPL-3.0-or-later
"""Choice sets for the guest models: the passthrough device *kind* (see
:class:`netbox_guests.models.GuestDevice`), the guest kind, the KVM firmware, the backup job's
vzdump and notification modes (:class:`netbox_guests.models.BackupJob`), and the LXC feature
flags. The guest kind, firmware and feature sets replace the ``guest-type`` / ``pve-bios`` /
``lxc-features`` CustomFieldChoiceSets that :class:`netbox_guests.models.GuestProfile`
supersedes -- as real enumerations on real model fields, so an invalid value is a validation
error rather than a string that only fails at converge time."""
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


class GuestTypeChoices(ChoiceSet):
    """Whether the guest is an LXC container or a KVM virtual machine. Both are modeled on core
    ``virtualization.VirtualMachine``; this is what distinguishes them, and it decides which half
    of :class:`netbox_guests.models.GuestProfile` applies."""
    CONTAINER = "container"
    VM = "vm"
    CHOICES = [
        (CONTAINER, "Container (LXC)", "cyan"),
        (VM, "Virtual Machine (KVM)", "blue"),
    ]


class PveBiosChoices(ChoiceSet):
    """KVM firmware. ``ovmf`` (UEFI) requires an EFI disk on the guest; ``seabios`` is the
    PVE default."""
    SEABIOS = "seabios"
    OVMF = "ovmf"
    CHOICES = [
        (SEABIOS, "SeaBIOS", "gray"),
        (OVMF, "OVMF (UEFI)", "purple"),
    ]


class BackupModeChoices(ChoiceSet):
    """vzdump backup mode (PVE ``mode=``): ``snapshot`` keeps the guest running, ``suspend``
    freezes it for the copy, ``stop`` shuts it down for a fully consistent image."""
    SNAPSHOT = "snapshot"
    SUSPEND = "suspend"
    STOP = "stop"
    CHOICES = (
        (SNAPSHOT, "Snapshot", "green"),
        (SUSPEND, "Suspend", "orange"),
        (STOP, "Stop", "red"),
    )


class BackupNotificationModeChoices(ChoiceSet):
    """How PVE reports a backup job's outcome (``notification-mode=``)."""
    AUTO = "auto"
    LEGACY_SENDMAIL = "legacy-sendmail"
    NOTIFICATION_SYSTEM = "notification-system"
    CHOICES = (
        (AUTO, "Auto", "gray"),
        (LEGACY_SENDMAIL, "Legacy sendmail", "orange"),
        (NOTIFICATION_SYSTEM, "Notification system", "blue"),
    )


class LxcFeatureChoices(ChoiceSet):
    """LXC feature flags (the PVE ``features=`` key). ``nesting`` is what lets a container run
    containers (podman/docker) and is the one most guests need; the rest widen the container's
    access to host facilities and are granted per guest, never fleet-wide."""
    NESTING = "nesting"
    KEYCTL = "keyctl"
    FUSE = "fuse"
    MOUNT = "mount"
    MKNOD = "mknod"
    CHOICES = [
        (NESTING, "nesting", "green"),
        (KEYCTL, "keyctl", "blue"),
        (FUSE, "fuse", "cyan"),
        (MOUNT, "mount", "orange"),
        (MKNOD, "mknod", "red"),
    ]
