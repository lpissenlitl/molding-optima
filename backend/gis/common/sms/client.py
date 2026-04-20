import logging

from gis.common.sms.api import SmsProviderNotSupport, SendSMSError
from gis.common.sms.providers import yp, telegram, luosimao

_LOGGER = logging.getLogger(__name__)


class SmsClient:
    def __init__(self):
        self.enabled_providers = dict()

    def init_providers(self, providers_conf):
        """
        {
          "enabled_providers": [
            "tg"
          ],
          "yp1": {
            "api_key": "xxxxxxxx",
            "sign": "【yp1】",
            "host": "http://xxx.com/api"
            "templates": {
              "default": "您的验证码是{}。如非本人操作，请忽略本短信"
            }
          },
          "yp2": {
            "api_key": "xxxxxxx",
            "sign": "【yp2】",
            "host": "http://xxx.com/api"
            "templates": {
              "default": "您的验证码是{}。如非本人操作，请忽略本短信"
            }
          },
          "lsm": {
            "api_key": "xxxxxx",
            "sign": "【lsm】",
            "host": "http://xxx.com/api"
            "templates": {
              "default": "您的验证码是{}。如非本人操作，请忽略本短信。"
            }
          },
          "tg": {
            "token": "xxxxxxxxx",
            "chat_id": "-311111111",
            "templates": {
              "default": "您的验证码是{}。如非本人操作，请忽略本短信。"
            }
          }
        }
        :param providers_conf: 配置
        """
        # 当前可用的所有短信服务提供商
        available_providers = {
            "yp1": yp.YPSmsProvider(**providers_conf["yp1"]),
            "yp2": yp.YPSmsProvider(**providers_conf["yp2"]),
            "lsm": luosimao.LuosimaoSmsProvider(**providers_conf["lsm"]),
            "tg": telegram.TelegramSmsProvider(**providers_conf["tg"]),
        }

        enabled_providers = dict()
        for name in providers_conf["enabled_providers"]:
            if name not in available_providers.keys():
                raise SmsProviderNotSupport(
                    "sms provider name [{}] is not supported".format(name)
                )
            enabled_providers[name] = available_providers[name]
        self.enabled_providers = enabled_providers
        assert enabled_providers

    def send(self, phone, *placeholders, template_name="default"):
        if not self.enabled_providers:
            raise SmsProviderNotSupport("no any provider")

        for name, provider in self.enabled_providers.items():
            try:
                _LOGGER.info(
                    "begin send sms to mobile: {}, provider: {}".format(phone, name)
                )
                provider.send(phone, template_name, *placeholders)
                break
            except SendSMSError as e:
                _LOGGER.warn(
                    "send sms to mobile fail, mobile: {}, provider: {}, error: {}".format(
                        phone, name, e
                    )
                )
