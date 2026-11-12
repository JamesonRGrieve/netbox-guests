# SPDX-License-Identifier: AGPL-3.0-or-later
"""The plugin reports the version of the distribution that is installed (what /api/status/ shows)."""
from importlib.metadata import version

from django.test import SimpleTestCase

from netbox_guests import __version__, config


class PluginVersionTest(SimpleTestCase):
    def test_version_is_the_installed_distribution(self):
        self.assertEqual(__version__, version("netbox-guests"))
        self.assertEqual(config.version, __version__)
        self.assertNotEqual(__version__, "0.0.1")
