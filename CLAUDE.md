# netbox-guests — Agent Operating Guide

Adapted from the sibling `../netbox-system-services` plugin (same engineering + test
discipline), re-targeted to **Proxmox guests** instead of management-plane services.

`netbox-guests` is an **AGPL-3.0** NetBox 4.6 plugin: a **native source of truth for Proxmox
guests** (LXC containers + KVM VMs), consumed by the `jamesonrgrieve/proxmox` Tofu provider to
*create* guests — **superseding the `netbox-proxbox` sync** (Proxmox→NetBox, wrong direction,
fields unused).

**Approach (operator decision 2026-09-27, superseding 2026-06-17): real plugin models, no core
fork.** Both guest kinds are modeled on core `virtualization.virtual-machine`; the network intent
is **native** — `VMInterface` (multi-NIC, MAC, 802.1Q `untagged_vlan`) + `ipam.IPAddress` on the
interface. Everything else PVE needs is a **model owned by this plugin**:

| Model | Scope | Holds |
|---|---|---|
| `GuestProfile` | OneToOne → VirtualMachine | guest kind, VMID, node, pool, storage, boot behaviour, the LXC half, the KVM half, OpenBao *references* |
| `GuestInterfaceConfig` | OneToOne → VMInterface | `bridge` + explicit `gateway` — the only per-NIC facts with no native home |
| `GuestMount` | FK → VirtualMachine | repeating `mpN` |
| `GuestDevice` | FK → VirtualMachine | repeating `devN` / raw-LXC passthrough |

The 2026-06-17 decision put the PVE scalars in typed **custom fields**. They were typed, but they
were still `extras.CustomField` rows — values in a JSON column, so `node` had no referential
integrity, `vmid` had no uniqueness, and a container could carry KVM-only intent that PVE would
silently ignore. The models fix exactly that. `customfields.py` and migration `0002` remain only
until `0008` drops the fields; **do not add a field there — add a column to the model.**

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
| `customfields.py` | SUPERSEDED — the legacy CF SPECS + `install`/`uninstall`, retained until `0008` removes the fields |
| `models.py` | `GuestProfile`, `GuestInterfaceConfig`, `GuestMount`, `GuestDevice` |
| `choices.py` | `DeviceKindChoices`, `GuestTypeChoices`, `PveBiosChoices`, `LxcFeatureChoices` — real enumerations, replacing the CustomFieldChoiceSets |
| `migrations/0001_initial.py` | `GuestMount` table (hand-authored; verify with `makemigrations --check --dry-run`) |
| `migrations/0002_custom_fields.py` | legacy: `RunPython(install, uninstall)` — installs the CFs |
| `migrations/0005_…` | `GuestProfile` + `GuestInterfaceConfig` tables, unique-VMID constraint |
| `migrations/0006_custom_fields_to_profile.py` | `RunPython(forward, backward)` — copies each guest's CF values into its profile. Idempotent (skips a guest that already has one) and reversible (writes the values back into `custom_field_data`). Reads `custom_field_data` directly, so it does not depend on the CF definitions still existing |
| `api/serializers.py`, `api/views.py`, `api/urls.py` | REST API (`NetBoxModelViewSet`) — endpoint `/api/plugins/guests/mounts/` |
| `filtersets.py` | `NetBoxModelFilterSet`: `virtual_machine_id`/`virtual_machine`, `mp`, `read_only`, search |
| `tables.py`, `forms.py`, `navigation.py`, `views.py`, `urls.py` | UI layer (generic NetBox views; no custom templates) |
| `graphql/__init__.py` | placeholder (no bespoke GraphQL type; `NetBoxModel` still exposes auto GraphQL) |

### Models — the guest SoT
- **Core `virtualization.virtual-machine`** (both LXC + KVM): native `name` (= real hostname,
  no `tofu-` prefix), `cluster` (FK — the PVE node/cluster), `status`, `role`, `vcpus`, `memory`,
  `disk`, `primary_ip`, `tags`.
- **`GuestProfile.guest_type`** (container | vm) distinguishes the two and decides which half of
  the profile applies; `clean()` rejects the other half.
- **Net intent (native):** one `VMInterface` per NIC + `ipam.IPAddress`; `bridge` + `gateway` live
  on `GuestInterfaceConfig` (the only homeless net fields).
- **PVE scalars (`GuestProfile` columns):** `vmid` (unique fleet-wide), `node` (FK → `dcim.Device`,
  PROTECT), `pool`, `storage`, `onboot`, `start`, `sandbox_of` (FK → the prod guest this copies),
  `description_template`; LXC: `swap`, `unprivileged` (default **true**), `features`, `ostemplate`;
  KVM: `template`, `image`, `iso`, `bios`, `cpu_type`, `sockets`, `numa`, `agent`, `cloud_init`.
- **Credentials:** `bao_secret_path` plus `has_admin_password` / `has_admin_token` /
  `has_db_password` / `has_secret_key`. A path and four existence flags — never a value.
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
