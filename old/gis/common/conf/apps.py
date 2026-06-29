import importlib
import logging

from django.apps import AppConfig
from django.conf import settings

from gis.common.conf.api import conf_client

_LOGGER = logging.getLogger(__name__)


class ConfConfig(AppConfig):
    name = "gis.common.conf"

    def ready(self):
        if hasattr(settings, "GCONF_CALLBACKS") and settings.GCONF_CALLBACKS:
            for conf_name, callback_path in settings.GCONF_CALLBACKS.items():
                mod_path, sep, callback_name = callback_path.rpartition(".")
                mod = importlib.import_module(mod_path)
                callback = getattr(mod, callback_name)
                conf_client.register_callbacks({conf_name: callback})

                _LOGGER.info(
                    "registry gconf callback: {} - {}".format(conf_name, callback_path)
                )
        else:
            _LOGGER.info("project has no any gconf callback")

        try:
            import uwsgidecorators

            @uwsgidecorators.postfork
            def execute_after_startup():
                start_conf()

        except ModuleNotFoundError:
            start_conf()


def start_conf():
    conf_client.start()
