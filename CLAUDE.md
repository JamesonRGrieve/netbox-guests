# netbox-guests — Agent Operating Guide

Adapted from the sibling `../netbox-system-services` plugin (same engineering + test
discipline), re-targeted to **Proxmox guests** instead of management-plane services.

`netbox-guests` is an **AGPL-3.0** NetBox 4.6 plugin: a **native source of truth for Proxmox
guests** (LXC containers + KVM VMs), consumed by the `jamesonrgrieve/proxmox` Tofu provider to
*create* guests — **superseding the `netbox-proxbox` sync** (Proxmox→NetBox, wrong direction,
fields unused).

**Approach (operator decision 2026-06-17): native VM + custom fields, no core fork.** Both guest
kinds are modeled on core `virtualization.virtual-machine` (distinguished by the `guest_type`
custom field). The network intent is **native** — `VMInterface` (multi-NIC, MAC, 802.1Q
`untagged_vlan`) + `ipam.IPAddress` on the interface — and the PVE scalars (`vmid`, `node`,
`storage`, `bios`, …) are typed **custom fields** installed by the data migration. The only
relational model this plugin owns is **`GuestMount`** (the repeating `mp0..N` structure that
does not fit a scalar custom field). This is "native" in the sense of real, typed, queryable
objects — **NOT** the `config_context` / proxbox CustomField-blob being retired.

**Why it matters:** the `hv/pve` Tofu module hardcodes `ip/gw = 192.168.{floor(vlan/10)}.{octet}`
and `vmid = vlan*1000+octet` because it computes addressing from vlan+octet. That formula cannot
express routable fleets (e.g. a CT on routable space like `203.0.113.x`). Explicit per-guest
`vmid`/`ip`/`gw`/`node`/`storage` here let the module read **literals** and de-hardcode. See
`DESIGN.md`.

**Secret policy (load-bearing):** the guest root credential is referenced by an OpenBao **path**
custom field (`root_credential_bao_path`); the password value is **never** stored in NetBox.
NetBox holds the structure; OpenBao holds the secret.

---

## Key Directives / Rules

### DO, ALWAYS:
- If functionality won't work without a parameter, make it a **required positional** parameter —
  never an optional one with an inline presence check.
- Any time you modify a source file, ensure its accompanying test under `netbox_guests/tests/`
  contains **comprehensive tests for the change WITHOUT MOCKS**, so `manage.py test
  netbox_guests` discovers them, and update any `.md` in the same directory that references the
  changed code.
- Write concise code (avoid obvious comments; use one-liners where possible).
- Critically analyze requirements and ask all necessary clarifying questions before implementing
  or refactoring.
- Phrase documentation for yourself (AI) and for autistic/ADHD humans: a clear architectural
  summary you could reconstruct the code from with 95% accuracy, with minimal snippets — **not**
  usage examples (the browsable REST/GraphQL schema is the usage reference).

### DO NOT, EVER, UNDER ANY CIRCUMSTANCE:
- Make assumptions, or answer with "is likely", "probably", or "might be".
- Store a guest root password or any other secret in a model field or custom field. Only a
  logical reference/path that keys OpenBao (`root_credential_bao_path`).
- Put the structured net intent in a JSON custom field. `vlan` → `VMInterface.untagged_vlan`,
  `ip` → `ipam.IPAddress` on the interface, `mac` → `VMInterface.mac_address`; only `bridge` +
  explicit `gateway` are interface custom fields.
- Re-introduce a `config_context` blob or a CustomField-used-as-data-blob — the thing this plugin
  retires.
- Use frame-local or thread-local state instead of passing data via parameters.
- Skip a failing test instead of fixing the root cause.
- Fix broken functionality while keeping the broken path as a fallback.
- **Mock the database, the ORM, the NetBox API test client, or any integration path.** Tests run
  against a **real test database** via NetBox's Django test framework — use real model instances
  (including real `virtualization` Cluster/VirtualMachine/VMInterface and real `extras`
  CustomField). Only pure utility functions may use mocks for isolation.

### Python / Django Guidelines:
- Import children of `datetime`: `from datetime import date` — **never** `import datetime`.
- Imports are package-relative inside `netbox_guests` (`from .models import GuestMount`), never
  `from netbox_guests.models import ...`. Imports of core use the real package path
  (`from virtualization.models import VirtualMachine`).
- Models inherit `netbox.models.NetBoxModel` (custom fields, tags, journaling, change logging,
  GraphQL — for free).
- **SPDX header on every source file**: `# SPDX-License-Identifier: AGPL-3.0-or-later`.

---

## Architecture (NetBox 4.6 plugin)

| File | Responsibility |
|------|----------------|
| `__init__.py` | `PluginConfig` — name `netbox_guests`, `base_url='guests'`, min/max NetBox version (tracks the sibling fleet; bump in lockstep when prod upgrades) |
| `customfields.py` | The canonical custom-field SPECS + `install`/`uninstall` (called by the data migration); the CF set installed on `virtualization.virtualmachine` / `.vminterface` |
| `models.py` | the single `GuestMount` model (FK → `virtualization.VirtualMachine`) |
| `migrations/0001_initial.py` | `GuestMount` table (hand-authored; verify with `makemigrations --check --dry-run`) |
| `migrations/0002_custom_fields.py` | `RunPython(install, uninstall)` — installs the CFs; depends on `extras __latest__` so the CF tables exist |
| `api/serializers.py`, `api/views.py`, `api/urls.py` | REST API (`NetBoxModelViewSet`) — endpoint `/api/plugins/guests/mounts/` |
| `filtersets.py` | `NetBoxModelFilterSet`: `virtual_machine_id`/`virtual_machine`, `mp`, `read_only`, search |
| `tables.py`, `forms.py`, `navigation.py`, `views.py`, `urls.py` | UI layer (generic NetBox views; no custom templates) |
| `graphql/__init__.py` | placeholder (no bespoke GraphQL type; `NetBoxModel` still exposes auto GraphQL) |

### Model & custom fields — the guest SoT
- **Core `virtualization.virtual-machine`** (both LXC + KVM): native `name` (= real hostname,
  no `tofu-` prefix), `cluster` (FK — the PVE node/cluster), `status`, `role`, `vcpus`, `memory`,
  `disk`, `primary_ip`, `tags`.
- **`guest_type`** custom field (select: container | vm) distinguishes the two.
- **Net intent (native):** one `VMInterface` per NIC + `ipam.IPAddress`; `bridge` + `gateway` are
  custom fields on the interface (the only homeless net fields).
- **PVE scalars (custom fields on the VM):** `vmid`, `node` (object → `dcim.Device`), `pool`,
  `storage`, `onboot`, `root_credential_bao_path`, `cloud_init_user`, `cloud_init_ssh_keys`;
  LXC: `swap`, `unprivileged`, `features` (multiselect), `ostemplate`; KVM: `image`, `iso`,
  `bios`, `cpu_type`, `agent`.
- **`GuestMount`** (FK → VirtualMachine): `mp`, `volume`, `path`, `read_only`; unique per
  `(virtual_machine, mp)`; CASCADE on VM delete. The host-side existence of the backing
  volume/dir is owned by Ansible/host bootstrap, not here.

The application/service layer that runs *on* a guest is the sibling `../netbox-services`
(`ServiceInstance.parent` → this VM, or a raw-OS `dcim.Device`).

---

## Testing (NO MOCKS — real DB, NetBox test framework)

- Tests live in `netbox_guests/tests/`, one module per layer (`test_models.py`, `test_api.py`,
  `test_filtersets.py`) plus `test_customfields.py` (asserts the data migration installed the CFs
  + choice sets on the right content types). `tests/utils.py` holds `make_vm`.
- Use NetBox's base classes from `utilities.testing`: `APIViewTestCases.*` (explicit CRUD mixins —
  no GraphQL type yet). They exercise model, API, and filters against a **real test database**.
- The `(virtual_machine, mp)` unique constraint means API `create_data` rows each use a distinct
  `mp`.
- **Never skip a failing test** — fix the root cause.
- **Run**: `python /opt/netbox/app/netbox/manage.py test netbox_guests --keepdb -v2`
  (or `pytest` with `pytest-django` + `DJANGO_SETTINGS_MODULE=netbox.settings`).
- **Verification owed (cannot run offline):** `makemigrations netbox_guests --check --dry-run`
  on an ephemeral NetBox, and a full test run — the custom-field model field names
  (`object_types`, `related_object_type`) target NetBox 4.6 and must be confirmed against the
  pinned version. `test_customfields.py` is the loud signal if they drift.

---

## Licensing
- **AGPL-3.0-or-later** (workspace production-IaC standard). SPDX header in every file.
