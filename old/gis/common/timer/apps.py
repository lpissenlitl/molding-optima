import importlib
import logging

from django.apps import AppConfig
from django.conf import settings

from .api import register_handler, get_task_handlers
from .executor import run

_LOGGER = logging.getLogger(__name__)


class TaskConfig(AppConfig):
    name = "gis.common.timer"

    def ready(self):
        _LOGGER.info("prepare registry all task handlers ...")
        if hasattr(settings, "TASK_HANDLERS") and settings.TASK_HANDLERS:
            for handler in settings.TASK_HANDLERS:
                mod_path, sep, cls_name = handler.rpartition(".")
                mod = importlib.import_module(mod_path)
                cls = getattr(mod, cls_name)()
                register_handler(cls)

                _LOGGER.info("registry success handler: {}".format(cls))
        else:
            _LOGGER.info("project has no any task handlers")

        # 如果配置了handler,则启动task服务
        if get_task_handlers():
            run()
