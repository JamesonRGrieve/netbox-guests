# SPDX-License-Identifier: AGPL-3.0-or-later
"""netbox-guests: a NetBox-native source of truth for Proxmox **guests** (LXC containers +
KVM VMs), consumed by the ``jamesonrgrieve/proxmox`` Tofu provider to *create* guests --
superseding the ``netbox-proxbox`` sync.

Both guest kinds are modeled on core ``virtualization.virtual-machine`` (distinguished by the
``guest_type`` custom field), with native ``VMInterface``/IPAM/802.1Q for the network intent
and typed **custom fields** for the PVE scalars (``vmid``, ``node``, ``storage``, ``bios`` …;
see :mod:`netbox_guests.customfields`). The only relational model this plugin owns is
:class:`netbox_guests.models.GuestMount` -- the one repeating PVE structure (``mp0..N``) that
does not fit a scalar custom field.

This is "native" in the sense of real, typed, queryable NetBox objects -- NOT the
``config_context`` / proxbox CustomField-blob approach being retired. The explicit per-guest
``vmid``/``ip``/``gw``/``node``/``storage`` is what de-hardcodes the ``hv/pve`` Tofu module
(whose vlan+octet formula cannot express routable-addressed fleets).

SECRET POLICY: the guest root credential is referenced by an OpenBao **path** custom field
(``root_credential_bao_path``); the password value is NEVER stored in NetBox.
"""
from netbox.plugins import PluginConfig

__version__ = "0.0.1"


class NetBoxGuestsConfig(PluginConfig):
    name = "netbox_guests"
    verbose_name = "NetBox Guests"
    description = "Native SoT for Proxmox guests (LXC + KVM): native VM + custom fields, consumed by the proxmox Tofu provider"
    version = __version__
    author = "Jameson"
    base_url = "guests"
    # Tracks the in-house plugin fleet / prod NetBox; bump in lockstep when prod upgrades.
    min_version = "4.6.0"
    max_version = "4.6.99"


config = NetBoxGuestsConfig
