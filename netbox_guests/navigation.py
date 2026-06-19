# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem

menu = PluginMenu(
    label="Guests",
    groups=(
        (
            "Proxmox Guests",
            (
                PluginMenuItem(
                    link="plugins:netbox_guests:guestmount_list",
                    link_text="Guest Mounts",
                    buttons=[
                        PluginMenuButton(
                            "plugins:netbox_guests:guestmount_add", "Add", "mdi mdi-plus-thick"
                        )
                    ],
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-server",
)
