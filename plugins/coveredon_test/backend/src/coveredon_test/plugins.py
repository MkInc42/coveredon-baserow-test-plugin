"""Covered On test plugin for Baserow 2.3.3.

Minimal plugin proving the install path works on our DMZ instance:
registers a single API endpoint at /api/coveredon-test/ping/.
"""
from baserow.core.registries import Plugin
from django.urls import path, include

from .api import urls as api_urls


class CoveredonTestPlugin(Plugin):
    type = "coveredon_test"

    def get_api_urls(self):
        return [
            path(
                "coveredon-test/",
                include(api_urls, namespace=self.type),
            ),
        ]
