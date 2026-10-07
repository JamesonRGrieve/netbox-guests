# SPDX-License-Identifier: AGPL-3.0-or-later
"""The guest layer is modeled on core ``virtualization.virtual-machine`` (LXC + KVM both), with
native ``VMInterface``/IPAM for the network intent and real plugin models for everything PVE
needs that core does not carry:

* :class:`GuestProfile` -- OneToOne per guest: guest kind, VMID, node, storage, boot behaviour,
  the LXC half, the KVM half, and OpenBao *references*. Supersedes the per-VM custom fields this
  plugin used to install, so ``node`` is a real FK, ``vmid`` has a real unique constraint, and
  mismatched intent fails validation instead of being silently dropped by PVE.
* :class:`GuestInterfaceConfig` -- OneToOne per NIC: bridge + explicit gateway, the only two
  per-interface facts with no native home.
* :class:`GuestMount` / :class:`GuestDevice` -- the repeating structures (``mpN``, ``devN``).
* :class:`BackupJob` -- a PVE scheduled vzdump job on one node. Its guest list is derived from the
  profiles that point at it (``GuestProfile.backup_job``), never typed.

Secrets are never stored: only an OpenBao path and ``has_*`` existence flags.
"""
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel

from .choices import (
    BackupModeChoices, BackupNotificationModeChoices, DeviceKindChoices, GuestTypeChoices,
    LxcFeatureChoices, PveBiosChoices,
)


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
    backup = models.BooleanField(default=False, help_text="Include in vzdump backups (backup=1).")

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
        default=0,
        help_text="Ordering index (dev0/dev1…); distinguishes multiple GPUs on one guest.",
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


class BackupJob(NetBoxModel):
    """A PVE scheduled backup job (``/cluster/backup/<job_id>``): when, where and how vzdump backs
    up a set of guests on one node.

    The guest list is NOT a column. It is derived from the :class:`GuestProfile` rows whose
    ``backup_job`` points here (:attr:`vmids`), so adding a guest to backups is a property of the
    guest, and a list typed by hand can never drift from the guests that exist. ``node`` scopes the
    job: each PVE host is its own cluster, so a job only ever backs up that node's guests."""

    node = models.ForeignKey(
        "dcim.Device", on_delete=models.PROTECT, related_name="backup_jobs",
        help_text="PVE node (its own cluster) the job runs on.",
    )
    job_id = models.CharField(
        max_length=64,
        help_text="PVE job id (the /cluster/backup/<id> key), e.g. backup-2db1d3a9-96c6.",
    )
    storage = models.CharField(max_length=255, help_text="PVE storage the backups are written to.")
    schedule = models.CharField(
        max_length=128, help_text="systemd calendar event in the node's local time (e.g. 21:00).",
    )
    mode = models.CharField(
        max_length=16, choices=BackupModeChoices, default=BackupModeChoices.SNAPSHOT,
        help_text="vzdump mode.",
    )
    enabled = models.BooleanField(default=True, help_text="Whether the schedule runs.")
    notes_template = models.CharField(
        max_length=1024, blank=True,
        help_text="Template for each backup's notes (e.g. {{guestname}}). Never include a secret.",
    )
    repeat_missed = models.BooleanField(
        default=False, help_text="Run a missed schedule as soon as the node is back.",
    )
    notification_mode = models.CharField(
        max_length=32, choices=BackupNotificationModeChoices,
        default=BackupNotificationModeChoices.AUTO, help_text="How PVE reports the outcome.",
    )
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("node", "job_id")
        verbose_name = "Backup Job"
        constraints = (
            models.UniqueConstraint(
                fields=("node", "job_id"), name="netbox_guests_backupjob_unique_node_job_id",
            ),
        )

    def __str__(self):
        return f"{self.node}: {self.job_id}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_guests:backupjob", args=[self.pk])

    @property
    def vmids(self):
        """The VMIDs this job backs up, ascending: every profile pointing here that has a VMID."""
        return sorted(
            self.guests.filter(vmid__isnull=False).values_list("vmid", flat=True)
        )


class GuestProfile(NetBoxModel):
    """The PVE provisioning intent for one guest, as real typed columns.

    Supersedes the per-VM custom fields the plugin used to install (``guest_type``, ``vmid``,
    ``node``, ``storage``, …). Those were typed, but they were still ``extras.CustomField`` rows:
    a value written into a JSON blob on the VM, with no referential integrity on ``node``, no
    uniqueness on ``vmid``, and no way to require the pair that PVE requires together. A OneToOne
    profile gives each field a column, ``node`` a real FK, ``vmid`` a real unique constraint, and
    ``clean()`` a place to reject a container carrying KVM-only intent.

    One row per guest, created on demand -- a VM with no profile is simply not
    pipeline-provisioned, which is the same meaning an empty custom field carried.

    Secrets are still absent by policy: ``bao_secret_path`` is a *reference* into OpenBao and the
    ``has_*`` booleans only record that a secret exists, so a consumer knows to read it without
    NetBox ever holding one."""

    virtual_machine = models.OneToOneField(
        "virtualization.VirtualMachine", on_delete=models.CASCADE, related_name="guest_profile"
    )
    guest_type = models.CharField(
        max_length=16, choices=GuestTypeChoices,
        help_text="LXC container or KVM virtual machine. Decides which fields below apply.",
    )

    # --- placement ---
    vmid = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Explicit Proxmox VMID. Unique fleet-wide; replaces the vlan*1000+octet formula.",
    )
    node = models.ForeignKey(
        "dcim.Device", on_delete=models.PROTECT, null=True, blank=True,
        related_name="hosted_guests",
        help_text="PVE node the guest runs on. A real FK, so the node cannot be deleted out from "
                  "under its guests.",
    )
    pool = models.CharField(max_length=128, blank=True, help_text="PVE resource pool.")
    storage = models.CharField(
        max_length=255, blank=True, help_text="PVE storage backing the rootfs / disk."
    )
    onboot = models.BooleanField(default=False, help_text="Start the guest when the node boots.")
    start = models.BooleanField(
        default=False, help_text="Start the guest immediately on creation."
    )
    # db_default keeps the column insertable by code that predates it, so rolling the plugin
    # back to v0.2.0 over a migrated database needs no restore.
    protection = models.BooleanField(
        default=False,
        db_default=False,
        help_text="PVE protection flag: the guest and its disks cannot be removed until it is "
                  "cleared. Set on control-plane guests.",
    )
    sandbox_of = models.ForeignKey(
        "virtualization.VirtualMachine", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="sandbox_guests",
        help_text="The production guest this one is a sandbox copy of. Set only on sandbox guests.",
    )
    backup_job = models.ForeignKey(
        "netbox_guests.BackupJob", on_delete=models.PROTECT, null=True, blank=True,
        related_name="guests",
        help_text="The scheduled backup job on this guest's node that backs it up. PROTECT: a job "
                  "is only deleted once no guest relies on it.",
    )
    description_template = models.TextField(
        blank=True,
        help_text="Template rendered into the PVE guest description. Never include a secret; "
                  "the description is visible to anyone with PVE read access.",
    )

    # --- credentials: references and existence only, never values ---
    bao_secret_path = models.CharField(
        max_length=255, blank=True,
        help_text="OpenBao KV path holding this guest's credentials. A reference, never a secret.",
    )
    has_admin_password = models.BooleanField(
        default=False, help_text="OpenBao holds an admin password for this guest."
    )
    has_admin_token = models.BooleanField(
        default=False, help_text="OpenBao holds an admin API token for this guest."
    )
    has_db_password = models.BooleanField(
        default=False, help_text="OpenBao holds a database password for this guest."
    )
    has_secret_key = models.BooleanField(
        default=False, help_text="OpenBao holds an application secret key for this guest."
    )

    # --- LXC (guest_type=container) ---
    swap = models.PositiveIntegerField(
        null=True, blank=True, help_text="LXC swap size in MiB."
    )
    unprivileged = models.BooleanField(
        default=True, help_text="Run as an unprivileged container. Privileged is opt-out."
    )
    features = ArrayField(
        models.CharField(max_length=32, choices=LxcFeatureChoices),
        default=list, blank=True,
        help_text="LXC feature flags granted to this container (PVE features=).",
    )
    ostemplate = models.CharField(
        max_length=255, blank=True, help_text="LXC ostemplate volume id the guest is built from."
    )

    # --- KVM (guest_type=vm) ---
    template = models.CharField(
        max_length=255, blank=True, help_text="Template the guest is cloned from."
    )
    image = models.CharField(
        max_length=255, blank=True, help_text="Disk image / import source."
    )
    iso = models.CharField(max_length=255, blank=True, help_text="ISO mounted as a cdrom.")
    bios = models.CharField(
        max_length=16, choices=PveBiosChoices, blank=True, help_text="KVM firmware."
    )
    cpu_type = models.CharField(
        max_length=64, blank=True, help_text="KVM CPU type (e.g. host)."
    )
    sockets = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="CPU sockets. vcpus on the VM is the total; this is how they are split.",
    )
    numa = models.BooleanField(default=False, help_text="Expose a NUMA topology to the guest.")
    agent = models.BooleanField(default=False, help_text="Enable the qemu-guest-agent.")
    cloud_init = models.BooleanField(
        default=False, help_text="Provision the guest via cloud-init."
    )

    class Meta:
        ordering = ["virtual_machine"]
        verbose_name = "Guest Profile"
        constraints = [
            models.UniqueConstraint(
                fields=["vmid"], name="netbox_guests_guestprofile_unique_vmid",
                condition=models.Q(vmid__isnull=False),
            ),
        ]

    def __str__(self):
        return f"{self.virtual_machine}: {self.get_guest_type_display()}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_guests:guestprofile", args=[self.pk])

    def get_guest_type_color(self):
        return GuestTypeChoices.colors.get(self.guest_type)

    def clean(self):
        """Reject intent that belongs to the other guest kind. PVE would silently ignore it, which
        is worse than failing here -- the SoT would claim something the guest does not have."""
        super().clean()
        container_only = {
            "swap": self.swap, "features": self.features, "ostemplate": self.ostemplate,
        }
        vm_only = {
            "image": self.image, "iso": self.iso, "bios": self.bios, "cpu_type": self.cpu_type,
            "numa": self.numa, "agent": self.agent,
        }
        if self.guest_type == GuestTypeChoices.CONTAINER:
            offenders = sorted(k for k, v in vm_only.items() if v not in (None, "", False, []))
            if offenders:
                raise ValidationError(
                    {k: "Not applicable to a container guest." for k in offenders}
                )
        elif self.guest_type == GuestTypeChoices.VM:
            offenders = sorted(
                k for k, v in container_only.items() if v not in (None, "", False, [])
            )
            if offenders:
                raise ValidationError(
                    {k: "Not applicable to a KVM guest." for k in offenders}
                )
        if self.sandbox_of_id and self.sandbox_of_id == self.virtual_machine_id:
            raise ValidationError({"sandbox_of": "A guest cannot be a sandbox of itself."})
        if self.backup_job_id:
            if self.vmid is None:
                raise ValidationError(
                    {"backup_job": "Set vmid: a backup job selects guests by VMID."}
                )
            if self.backup_job.node_id != self.node_id:
                raise ValidationError(
                    {"backup_job": "The backup job must run on this guest's node."}
                )


class GuestInterfaceConfig(NetBoxModel):
    """The two per-NIC PVE facts with no native NetBox home: which host bridge the NIC attaches
    to, and its explicit default gateway.

    Everything else about a guest NIC is already native and stays there -- the VLAN is
    ``VMInterface.untagged_vlan``, the address is an ``ipam.IPAddress`` on the interface, the MAC
    is ``VMInterface.mac_address``. The gateway is here rather than derived because the
    lowest-usable-address assumption is wrong for routable space."""

    interface = models.OneToOneField(
        "virtualization.VMInterface", on_delete=models.CASCADE, related_name="guest_config"
    )
    bridge = models.CharField(
        max_length=64, blank=True, help_text="PVE host bridge this NIC attaches to (e.g. vmbr0)."
    )
    gateway = models.GenericIPAddressField(
        null=True, blank=True,
        help_text="Explicit default gateway for this NIC. Set it: the lowest-usable-address "
                  "guess is wrong on routable space.",
    )

    class Meta:
        ordering = ["interface"]
        verbose_name = "Guest Interface Config"

    def __str__(self):
        return f"{self.interface}: {self.bridge or 'no bridge'}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_guests:guestinterfaceconfig", args=[self.pk])
