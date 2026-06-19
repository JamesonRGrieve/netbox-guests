# SPDX-License-Identifier: AGPL-3.0-or-later
"""Canonical custom-field definitions for the guest layer, installed on core
``virtualization.virtualmachine`` and ``virtualization.vminterface`` by the data migration
(:func:`install`) and asserted by ``tests/test_customfields.py``.

These are the PVE scalars that have no native NetBox home. The *structured* net intent is NOT
here -- it is native: ``vlan`` → ``VMInterface.untagged_vlan``, ``ip`` → ``ipam.IPAddress`` on
the interface, ``mac`` → ``VMInterface.mac_address``; only ``bridge`` and the explicit
``gateway`` need a custom field (on the interface). Repeating mounts are the :class:`.models.GuestMount`
model. Secrets stay in OpenBao -- ``root_credential_bao_path`` holds a *reference*, never the secret.

Field/relation names target NetBox 4.6 (``object_types`` M2M, ``related_object_type`` FK); the
``install`` helper guards the M2M name for older lines. Re-verify against the pinned NetBox with
``makemigrations --check`` + a test run on an ephemeral instance.
"""

# (app_label, model) tuples for the content types the fields attach / relate to.
_VM = ("virtualization", "virtualmachine")
_VMINTERFACE = ("virtualization", "vminterface")
_DEVICE = ("dcim", "device")

# CustomFieldChoiceSet name -> [(value, label), ...]
CHOICE_SETS = {
    "guest-type": [("container", "Container (LXC)"), ("vm", "Virtual Machine (KVM)")],
    "pve-bios": [("seabios", "SeaBIOS"), ("ovmf", "OVMF (UEFI)")],
    "lxc-features": [
        ("nesting", "nesting"), ("keyctl", "keyctl"), ("fuse", "fuse"),
        ("mount", "mount"), ("mknod", "mknod"),
    ],
}

# Each spec: name, label, type, objects[(app,model)], + optional choice_set / related_object /
# description / required / weight / group_name. Types are NetBox CustomField type literals.
SPECS = [
    # --- Guest identity / placement (on the VM) ---
    {"name": "guest_type", "label": "Guest type", "type": "select", "objects": [_VM],
     "choice_set": "guest-type", "required": True, "group_name": "Guest", "weight": 100,
     "description": "Container (LXC) or KVM virtual machine."},
    {"name": "vmid", "label": "VMID", "type": "integer", "objects": [_VM],
     "group_name": "Guest", "weight": 110,
     "description": "Explicit Proxmox VMID (replaces the vlan*1000+octet formula)."},
    {"name": "node", "label": "PVE node", "type": "object", "objects": [_VM],
     "related_object": _DEVICE, "group_name": "Guest", "weight": 120,
     "description": "PVE node (dcim.Device) the guest runs on."},
    {"name": "pool", "label": "PVE pool", "type": "text", "objects": [_VM],
     "group_name": "Guest", "weight": 130, "description": "PVE resource pool."},
    {"name": "storage", "label": "Storage", "type": "text", "objects": [_VM],
     "group_name": "Guest", "weight": 140, "description": "PVE storage for rootfs / disk."},
    {"name": "onboot", "label": "Start on boot", "type": "boolean", "objects": [_VM],
     "group_name": "Guest", "weight": 150, "description": "Start guest when the node boots."},
    {"name": "root_credential_bao_path", "label": "Root credential (OpenBao path)",
     "type": "text", "objects": [_VM], "group_name": "Guest", "weight": 160,
     "description": "OpenBao path for the guest root credential -- a reference, never the secret."},
    # --- Cloud-init (on the VM); network intent is native, not here ---
    {"name": "cloud_init_user", "label": "cloud-init user", "type": "text", "objects": [_VM],
     "group_name": "Cloud-init", "weight": 200, "description": "ciuser."},
    {"name": "cloud_init_ssh_keys", "label": "cloud-init SSH keys", "type": "longtext",
     "objects": [_VM], "group_name": "Cloud-init", "weight": 210,
     "description": "Authorized SSH public keys (newline-separated)."},
    # --- LXC-specific (on the VM; guest_type=container) ---
    {"name": "swap", "label": "Swap (MiB)", "type": "integer", "objects": [_VM],
     "group_name": "Container", "weight": 300, "description": "LXC swap size in MiB."},
    {"name": "unprivileged", "label": "Unprivileged", "type": "boolean", "objects": [_VM],
     "group_name": "Container", "weight": 310, "description": "LXC unprivileged container."},
    {"name": "features", "label": "LXC features", "type": "multiselect", "objects": [_VM],
     "choice_set": "lxc-features", "group_name": "Container", "weight": 320,
     "description": "LXC features (nesting, keyctl, fuse, mount, mknod)."},
    {"name": "ostemplate", "label": "OS template", "type": "text", "objects": [_VM],
     "group_name": "Container", "weight": 330, "description": "LXC ostemplate file id."},
    # --- KVM-specific (on the VM; guest_type=vm) ---
    {"name": "image", "label": "Disk image", "type": "text", "objects": [_VM],
     "group_name": "VM", "weight": 400, "description": "KVM disk image / import source."},
    {"name": "iso", "label": "ISO", "type": "text", "objects": [_VM],
     "group_name": "VM", "weight": 410, "description": "KVM ISO mounted as cdrom."},
    {"name": "bios", "label": "BIOS", "type": "select", "objects": [_VM],
     "choice_set": "pve-bios", "group_name": "VM", "weight": 420, "description": "KVM firmware."},
    {"name": "cpu_type", "label": "CPU type", "type": "text", "objects": [_VM],
     "group_name": "VM", "weight": 430, "description": "KVM CPU type (e.g. host)."},
    {"name": "agent", "label": "QEMU guest agent", "type": "boolean", "objects": [_VM],
     "group_name": "VM", "weight": 440, "description": "Enable the qemu-guest-agent."},
    # --- Per-interface net intent with no native home (on the VMInterface) ---
    {"name": "bridge", "label": "PVE bridge", "type": "text", "objects": [_VMINTERFACE],
     "group_name": "Guest network", "weight": 500,
     "description": "PVE bridge for this NIC (vlan → untagged_vlan, ip → IPAM, mac → native)."},
    {"name": "gateway", "label": "Gateway", "type": "text", "objects": [_VMINTERFACE],
     "group_name": "Guest network", "weight": 510,
     "description": "Explicit default gateway for this NIC (the lowest-usable formula is wrong for routable nets)."},
]


def _ct(apps, app_label, model):
    return apps.get_model("contenttypes", "ContentType").objects.get(app_label=app_label, model=model)


def install(apps, schema_editor=None):
    """Idempotently create the choice sets + custom fields. Safe to re-run (get_or_create)."""
    CustomField = apps.get_model("extras", "CustomField")
    CustomFieldChoiceSet = apps.get_model("extras", "CustomFieldChoiceSet")

    choice_sets = {}
    for name, choices in CHOICE_SETS.items():
        cs, _ = CustomFieldChoiceSet.objects.get_or_create(
            name=name, defaults={"extra_choices": [list(c) for c in choices]}
        )
        choice_sets[name] = cs

    for spec in SPECS:
        defaults = {
            "label": spec.get("label", ""),
            "type": spec["type"],
            "description": spec.get("description", ""),
            "required": spec.get("required", False),
            "weight": spec.get("weight", 100),
            "group_name": spec.get("group_name", ""),
        }
        if "choice_set" in spec:
            defaults["choice_set"] = choice_sets[spec["choice_set"]]
        if "related_object" in spec:
            defaults["related_object_type_id"] = _ct(apps, *spec["related_object"]).pk
        cf, _ = CustomField.objects.get_or_create(name=spec["name"], defaults=defaults)
        ct_ids = [_ct(apps, *obj).pk for obj in spec["objects"]]
        # NetBox 4.1+ renamed content_types -> object_types; guard for older lines.
        m2m = "object_types" if hasattr(cf, "object_types") else "content_types"
        getattr(cf, m2m).set(ct_ids)


def uninstall(apps, schema_editor=None):
    """Reverse of :func:`install` -- remove the custom fields + choice sets this plugin owns."""
    CustomField = apps.get_model("extras", "CustomField")
    CustomFieldChoiceSet = apps.get_model("extras", "CustomFieldChoiceSet")
    CustomField.objects.filter(name__in=[s["name"] for s in SPECS]).delete()
    CustomFieldChoiceSet.objects.filter(name__in=list(CHOICE_SETS)).delete()
