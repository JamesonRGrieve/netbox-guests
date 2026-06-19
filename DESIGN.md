# netbox-guests — Design

**Status:** design resolved 2026-06-17 (operator decisions); not yet implemented.

Model Proxmox **guests** (LXC containers + KVM VMs) as **NetBox-native intent** — the
single source of truth the in-house `jamesonrgrieve/proxmox` Tofu provider reads to
*create* guests — **superseding the unused `netbox-proxbox` sync**. Pairs with
[`netbox-services`](../netbox-services/DESIGN.md) (the application layer whose
`ServiceInstance.parent` targets a guest **or a raw-OS device**).

---

## 1. Approach — native VM + custom fields, no core fork

NetBox core `virtualization` has `Cluster / VirtualMachine / VMInterface / VirtualDisk`
but **no container type**. Rather than fork core to add a first-class
`virtualization.container` — a per-release patch-rebase burden with **no precedent in
this workspace** (every in-house `netbox-*` plugin is a related-model / custom-field
plugin; none patches core) — **both LXC containers and KVM VMs are modeled on core
`virtualization.virtual-machine`**, distinguished by a `guest_type` custom field. This
stays plugin-scoped and upgrade-safe.

**"Native" here means real, typed, queryable NetBox objects** — native `VMInterface` +
IPAM + 802.1Q VLAN + MAC, plus typed **custom fields** for the PVE scalars that have no
native home — **not** the `config_context` / proxbox CustomField-blob approach being
retired. The one semantic cost: an LXC CT shows in the UI as a "virtual machine." For a
Tofu-feeding SoT that is acceptable, and it matches what the `hv/pve` reader already does
(the `guest_type` split in `netbox_services.tf`).

Custom-field definitions and the one related model ship **as code** in the
`netbox_guests` plugin (`PluginConfig` + data migration), mirroring
`netbox-system-services`. Pin to the **latest** NetBox release (upgrade prod NetBox +
bump sibling plugins' min/max to match).

---

## 2. Model

### On core `virtualization.virtual-machine` (native fields, as-is)
`name` (= the **real hostname**, no `tofu-` prefix), `cluster` (FK — the PVE
node/cluster), `status`, `role`, `platform`, `tenant`, `vcpus`, `memory`, `disk`,
`primary_ip`, `comments`, `tags`.

### Native interfaces + IPAM (one `VMInterface` per NIC)
Gives **multi-NIC**, `mac_address`, `mtu`, and 802.1Q `untagged_vlan` (→ `ipam.VLAN`)
for free. **IP**: a native `ipam.IPAddress` assigned to the `VMInterface` (which is a
valid IPAM assignment target — no allowlist problem). **Gateway**: an **explicit custom
field** (the module's lowest-usable formula is wrong for a routable fleet whose gateway is e.g. `.126`). **Per-iface
`bridge`**: a custom field on the `VMInterface` — the only net field with no native home
(vlan → `untagged_vlan`, ip → IPAM, mac → native).

### Custom fields on the VM (typed PVE scalars)
`guest_type` (select: `container`|`vm`), `vmid` (int), `node` (object → `dcim.Device`),
`storage`, `pool`, `onboot`, `unprivileged`, `features` (nesting…), `swap`,
`ostemplate` (CT) / `image`/`iso` (VM), `bios`, `cpu_type`, `agent`,
`cloud_init` (user / ssh_keys / network), and an **OpenBao path** for the guest root
credential (value lives in OpenBao; the password is never stored, and the module stops
writing it into the PVE description).

### `GuestMount` related model (thin, FK → VM)
`mp` index, `volume`, `path` — the only genuinely-repeating structure that does not fit
a scalar CF. Build only if guests actually use mounts; otherwise flat `mp0..N` CFs
suffice.

### Excluded — belongs to `netbox-services`
`app_playbook`, `app_vars`, `port`, application credentials. The guest layer is
**box-level only**; the application layer is the paired plugin's `ServiceInstance`.

---

## 3. Why this matters — kills the `hv/pve` hardcoding

The `hv/pve` module hardcodes `ip/gw = 192.168.{floor(vlan/10)}.{octet}` and
`vmid = vlan*1000+octet` (`tofu/opentofu/hv/pve/locals.tf:128-136`) **because it computes
addressing from vlan+octet**. That formula cannot express a routable-addressed fleet (CTs on
routable space), so those guests are **un-buildable today**. With guests carrying
**explicit** vmid + IP (IPAM) + gw (CF) + node + storage + per-iface bridge, the module
**reads literals** → a routable `203.0.113.x/25`, gw `.126`, an explicit vmid just works; no
hardcoding, no per-client special-casing.

De-hardcoding is a **full module refactor**, not a formula swap. The module today is
single-node (`var.proxmox_node`), single-VLAN (`pool = "vlan-${var.vlan}"`,
`pools.tf:17`), single-bridge (`var.bridge`), single auto-detected `local.storage`,
**name-keyed** `for_each` (`locals.tf:192,207`), and force-prefixes hostnames `tofu-`
(`containers.tf:117`, `vm.tf:90`). The refactor:

- **vmid-keyed `for_each`** + a one-time `moved {}` pass (stable-key rule,
  `ai-prompts/tofu.md:145-160`) — a rename must not become destroy+recreate.
- **real hostname** (drop the `tofu-` prefix) — the #1 0-diff-adoption blocker.
- **per-guest** node / storage / pool, **per-iface** bridge.
- **multi-NIC** — the module emits only `net0` (`containers.tf:132`, `vm.tf:110`);
  §7 needs a second NIC. Native `VMInterface` makes this free on the NetBox side.

The generic `proxmox_object` / `proxmox_task` provider needs **no change** — it is a REST
shim; the module does all field shaping. A separate host (its own API endpoint) is a
**dedicated root with its own provider config**, not a provider-code change.

---

## 4. Consumers & retirement

- **`jamesonrgrieve/proxmox` provider** (+ `hv/pve` module): reads guest intent →
  creates CT/VM. Module de-hardcoded to read explicit fields; **provider unchanged**.
- **`netbox-services`**: `ServiceInstance.parent` → a guest VM **or a raw-OS
  `dcim.Device`**. No separate Container content-type (containers are VMs).
- **Retire `netbox-proxbox`** once guests are modeled here. NetBox becomes upstream;
  Proxmox is reconciled *from* NetBox.

---

## 5. Migration / adoption

Import-first, **0-diff** (adopt, never recreate):

- Reclassify existing guests (the WP fleet, lab CTs/VMs) onto the VM model +
  `guest_type` CF + native `VMInterface`/IPAM. The reclassification must land **before**
  any `ServiceInstance` so the GFK target row and its content-type are stable.
- 0-diff first-plan prerequisites: vmid-keyed `for_each`, real hostname (drop `tofu-`),
  explicit fields, and capturing live **MACs** onto each `VMInterface`.
- **Interim (unblock a routable-fleet CT ahead of the plugin):** de-hardcode the module to read the
  explicit fields from the existing `local_context_data`, **logged in
  `CONFIG_CONTEXT_HERESY.md`** and ratcheted to native CFs when the plugin lands.

---

## 6. Build sequence (dependency DAG)

1. **NetBox → latest**; bump sibling plugins' min/max.
2. **Tofu de-hardcode (full refactor)** → 0-diff plan **unblocks the routable fleet**
   (interim source: config_context, logged as heresy).
3. **`netbox_guests` plugin** (`PluginConfig` + migration: CFs + `GuestMount`);
   importer adopts live guests to 0-diff; **retire proxbox**.
4. **Flip the module reader** config_context → native CFs/objects (the
   `prod-lab/docs/netbox-modeling.md §3` merge pattern; module contract unchanged);
   delete the config_context fallback guest-by-guest.
5. **`netbox-services`** (GFK targets now stable).
6. **§7 HA** — last (see §7).

---

## 7. HA mirror guests + failover wiring

When a guest hosts HA-mirror services (see
[`../netbox-services/DESIGN.md`](../netbox-services/DESIGN.md) §7 `high_availability_of`),
the guest + edge wiring it needs:

- **Mirror guest** — a normal guest VM on the standby host (e.g. a mirror CT on a
  segregated HA VLAN / routable space), the **hot** peer of the primary CT.
- **Routable repl NIC** — a **second `VMInterface`** carrying a routable **`/32`**
  (dedicated repl range) added to the house↔site `wg2` AllowedIPs via `netbox-wireguard`.
  Content rsync + MariaDB master-master ride this; **live HTTP rides the edge WAN**.
  Native multi-NIC makes the second interface free.
- **HAProxy backup registration** (ingress) — a new **`LBMemberHA`** (backup-member)
  model in the in-house **`netbox-load-balancing-acl`** plugin (FK → base Member/Pool +
  `backup` bool — **not** a change to the third-party `netbox-load-balancing` base) →
  joined in `net/routers` → emits the HAProxy `backup` keyword onto the edge router.

**§7 dependency chain (each must reach 0-diff first):** the multi-NIC guest (§3), the
edge-router `net/routers` import-first adoption, the `LBMemberHA` model + its `net/routers` join,
a `netbox-wireguard` AllowedIPs reader in `net/routers`, and a repl `/32` IPAM
allocation. **Sequence §7 last.** The `high_availability_of` model, per-type
`ha_strategy`, and the reconciler live in `../netbox-services/DESIGN.md` §7.

---

## 8. References

- `ansible/CLAUDE.md` EOS.4 (NetBox-upstream SoT direction).
- `prod-lab/docs/netbox-modeling.md` (SoT boundary; native > plugin > core >
  config_context; the §3 reader merge pattern), `netbox-tofu-bao.md` (wiring).
- `tofu/opentofu/hv/pve/{containers,vm,locals,networking,pools,netbox_services}.tf`
  (the hardcoded addressing + single-everything module this fixes).
- `ai-prompts/tofu.md` (provider/module standards: stable-key `for_each`, ephemeral
  secrets, import-first / 0-diff).
- Structural reference: `netbox-system-services` (plugin layout to mirror).
- Sibling: [`netbox-services`](../netbox-services/DESIGN.md) (application layer).
