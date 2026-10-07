# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem

menu = PluginMenu(
    label="Guests",
    groups=(
        (
            "Proxmox Guests",
            (
                PluginMenuItem(
                    link="plugins:netbox_guests:guestprofile_list",
                    link_text="Guest Profiles",
                    buttons=[
                        PluginMenuButton(
                            "plugins:netbox_guests:guestprofile_add", "Add", "mdi mdi-plus-thick"
                        )
                    ],
                ),
                PluginMenuItem(
                    link="plugins:netbox_guests:guestinterfaceconfig_list",
                    link_text="Guest Interface Configs",
                    buttons=[
                        PluginMenuButton(
                            "plugins:netbox_guests:guestinterfaceconfig_add", "Add", "mdi mdi-plus-thick"
                        )
                    ],
                ),
                PluginMenuItem(
                    link="plugins:netbox_guests:guestmount_list",
                    link_text="Guest Mounts",
                    buttons=[
                        PluginMenuButton(
                            "plugins:netbox_guests:guestmount_add", "Add", "mdi mdi-plus-thick"
                        )
                    ],
                ),
                PluginMenuItem(
                    link="plugins:netbox_guests:backupjob_list",
                    link_text="Backup Jobs",
                    buttons=[
                        PluginMenuButton(
                            "plugins:netbox_guests:backupjob_add", "Add", "mdi mdi-plus-thick"
                        )
                    ],
                ),
                PluginMenuItem(
                    link="plugins:netbox_guests:guestdevice_list",
                    link_text="Guest Devices",
                    buttons=[
                        PluginMenuButton(
                            "plugins:netbox_guests:guestdevice_add", "Add", "mdi mdi-plus-thick"
                        )
                    ],
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-server",
)
