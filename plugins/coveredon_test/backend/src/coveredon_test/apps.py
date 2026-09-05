from baserow.core.registries import plugin_registry
from django.apps import AppConfig


class CoveredonTestConfig(AppConfig):
    name = "coveredon_test"

    def ready(self):
        from .plugins import CoveredonTestPlugin

        plugin_registry.register(CoveredonTestPlugin())
