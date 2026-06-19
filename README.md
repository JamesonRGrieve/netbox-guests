# netbox-guests

NetBox-native modeling of Proxmox **guests** (LXC containers + KVM VMs) as intent — core
`virtualization.virtual-machine` + a `guest_type` custom field (no core fork) — the
source of truth for the `jamesonrgrieve/proxmox` Tofu provider, **superseding
`netbox-proxbox`**.

**Status:** design resolved 2026-06-17; plugin scaffold present (untested — needs a NetBox env).
See **[DESIGN.md](DESIGN.md)** — model, the native-VM-plus-CF approach, the `hv/pve`
de-hardcoding rationale, and migration — and **[CLAUDE.md](CLAUDE.md)** (architecture + test
discipline). Pairs with the sibling [`netbox-services`](../netbox-services) (application layer).

## Layout

```
netbox_guests/
  __init__.py        PluginConfig (base_url 'guests')
  models.py          GuestMount (FK → virtualization.VirtualMachine)
  customfields.py    canonical CF specs + install/uninstall (run by the migration)
  migrations/        0001 GuestMount table · 0002 custom-field install
  api/               REST (/api/plugins/guests/mounts/)
  filtersets.py forms.py tables.py views.py urls.py navigation.py
  graphql/           placeholder (auto GraphQL via NetBoxModel)
  tests/             real-DB tests (models, api, filtersets, customfields) + utils
```

The net intent is native (`VMInterface`/IPAM/802.1Q); `bridge` + explicit `gateway` and the PVE
scalars (`vmid`, `node`, `storage`, `bios`, cloud-init …) are typed custom fields. The guest root
credential is an OpenBao **path** reference (`root_credential_bao_path`), never the password.

## Develop / test

```
python /opt/netbox/app/netbox/manage.py test netbox_guests --keepdb -v2
python /opt/netbox/app/netbox/manage.py makemigrations netbox_guests --check --dry-run
```

Both require a NetBox environment; the custom-field migration targets NetBox 4.6 field names and
must be verified against the pinned version.
