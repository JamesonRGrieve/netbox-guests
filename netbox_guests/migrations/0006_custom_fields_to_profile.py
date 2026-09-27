# SPDX-License-Identifier: AGPL-3.0-or-later
# Data migration: copy the per-VM and per-VMInterface custom-field values this plugin installed in
# 0002 into the GuestProfile / GuestInterfaceConfig rows created in 0005.
#
# Custom-field values live in each object's `custom_field_data` JSON column, keyed by field name.
# The forward pass reads that column, so it needs no CustomField lookup and cannot be affected by
# a field having already been renamed or removed. It is IDEMPOTENT: a guest that already has a
# profile is left untouched, so re-running after a partial apply is safe.
#
# It is also REVERSIBLE: the backward pass writes the model values back into custom_field_data and
# deletes the rows, so a rollback restores exactly what the custom fields held. That matters
# because the custom fields are NOT dropped here -- 0007 does that, only once every consumer reads
# the models.
from django.db import migrations

# custom field name -> (profile field, coercion)
_STR = lambda v: str(v).strip()                                        # noqa: E731
_INT = lambda v: int(v)                                                # noqa: E731
_BOOL = lambda v: bool(v)                                              # noqa: E731
_LIST = lambda v: [str(x) for x in v] if isinstance(v, (list, tuple)) else [str(v)]  # noqa: E731

VM_FIELDS = {
    "guest_type": ("guest_type", _STR),
    "vmid": ("vmid", _INT),
    "pool": ("pool", _STR),
    "storage": ("storage", _STR),
    "onboot": ("onboot", _BOOL),
    "start": ("start", _BOOL),
    "description_template": ("description_template", _STR),
    "bao_secret_path": ("bao_secret_path", _STR),
    "has_admin_password": ("has_admin_password", _BOOL),
    "has_admin_token": ("has_admin_token", _BOOL),
    "has_db_password": ("has_db_password", _BOOL),
    "has_secret_key": ("has_secret_key", _BOOL),
    "swap": ("swap", _INT),
    "unprivileged": ("unprivileged", _BOOL),
    "features": ("features", _LIST),
    "ostemplate": ("ostemplate", _STR),
    "template": ("template", _STR),
    "image": ("image", _STR),
    "iso": ("iso", _STR),
    "bios": ("bios", _STR),
    "cpu_type": ("cpu_type", _STR),
    "sockets": ("sockets", _INT),
    "numa": ("numa", _BOOL),
    "agent": ("agent", _BOOL),
    "cloud_init": ("cloud_init", _BOOL),
}
# Object-type custom fields hold the referenced object's PK.
VM_FK_FIELDS = {"node": "node_id", "sandbox_of": "sandbox_of_id"}
IFACE_FIELDS = {"bridge": ("bridge", _STR)}
IFACE_FK_FIELDS = {}


def _clean(value):
    """Treat an unset custom field the way a lookup() with no default did: as absent."""
    return value not in (None, "", [], {})


def forward(apps, schema_editor):
    VirtualMachine = apps.get_model("virtualization", "VirtualMachine")
    VMInterface = apps.get_model("virtualization", "VMInterface")
    Device = apps.get_model("dcim", "Device")
    GuestProfile = apps.get_model("netbox_guests", "GuestProfile")
    GuestInterfaceConfig = apps.get_model("netbox_guests", "GuestInterfaceConfig")

    device_ids = set(Device.objects.values_list("pk", flat=True))
    vm_ids = set(VirtualMachine.objects.values_list("pk", flat=True))

    for vm in VirtualMachine.objects.all().iterator():
        if GuestProfile.objects.filter(virtual_machine_id=vm.pk).exists():
            continue
        data = vm.custom_field_data or {}
        if not any(_clean(data.get(name)) for name in list(VM_FIELDS) + list(VM_FK_FIELDS)):
            continue  # nothing recorded for this guest -> no profile, same meaning as before
        kwargs = {}
        for cf_name, (field, coerce) in VM_FIELDS.items():
            raw = data.get(cf_name)
            if _clean(raw):
                try:
                    kwargs[field] = coerce(raw)
                except (TypeError, ValueError):
                    continue  # a value the column cannot hold is left for the audit, not guessed
        for cf_name, field in VM_FK_FIELDS.items():
            raw = data.get(cf_name)
            if not _clean(raw):
                continue
            try:
                pk = int(raw)
            except (TypeError, ValueError):
                continue
            valid = device_ids if field == "node_id" else vm_ids
            if pk in valid and not (field == "sandbox_of_id" and pk == vm.pk):
                kwargs[field] = pk
        # guest_type is the one required column; an LXC-shaped profile with no recorded kind is a
        # container, which is what every such guest in the fleet is.
        if not kwargs.get("guest_type"):
            kwargs["guest_type"] = "container"
        GuestProfile.objects.create(virtual_machine_id=vm.pk, **kwargs)

    for iface in VMInterface.objects.all().iterator():
        if GuestInterfaceConfig.objects.filter(interface_id=iface.pk).exists():
            continue
        data = iface.custom_field_data or {}
        gateway = data.get("gateway")
        kwargs = {}
        for cf_name, (field, coerce) in IFACE_FIELDS.items():
            if _clean(data.get(cf_name)):
                kwargs[field] = coerce(data[cf_name])
        if _clean(gateway):
            kwargs["gateway"] = str(gateway).split("/")[0].strip()
        if kwargs:
            GuestInterfaceConfig.objects.create(interface_id=iface.pk, **kwargs)


def backward(apps, schema_editor):
    """Write the model values back into custom_field_data and drop the rows, so the state before
    0006 is restored exactly -- including for guests whose profile was edited since."""
    VirtualMachine = apps.get_model("virtualization", "VirtualMachine")
    VMInterface = apps.get_model("virtualization", "VMInterface")
    GuestProfile = apps.get_model("netbox_guests", "GuestProfile")
    GuestInterfaceConfig = apps.get_model("netbox_guests", "GuestInterfaceConfig")

    for profile in GuestProfile.objects.all().iterator():
        vm = VirtualMachine.objects.get(pk=profile.virtual_machine_id)
        data = dict(vm.custom_field_data or {})
        for cf_name, (field, _coerce) in VM_FIELDS.items():
            value = getattr(profile, field)
            if value not in (None, "", []):
                data[cf_name] = value
        for cf_name, field in VM_FK_FIELDS.items():
            value = getattr(profile, field)
            if value:
                data[cf_name] = value
        vm.custom_field_data = data
        vm.save(update_fields=["custom_field_data"])
    GuestProfile.objects.all().delete()

    for cfg in GuestInterfaceConfig.objects.all().iterator():
        iface = VMInterface.objects.get(pk=cfg.interface_id)
        data = dict(iface.custom_field_data or {})
        if cfg.bridge:
            data["bridge"] = cfg.bridge
        if cfg.gateway:
            data["gateway"] = cfg.gateway
        iface.custom_field_data = data
        iface.save(update_fields=["custom_field_data"])
    GuestInterfaceConfig.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("netbox_guests", "0005_guestprofile_guestinterfaceconfig")]
    operations = [migrations.RunPython(forward, backward)]
