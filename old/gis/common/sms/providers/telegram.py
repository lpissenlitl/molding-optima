"""
Telegram模拟短信发送

请先加入机器短信发送群，当触发短信发送时，机器人会在对应群里发送短信内容。

"""
import logging

import requests
from requests import RequestException

from gis.common.sms.api import SmsProvider, SendSMSError

_LOGGER = logging.getLogger(__name__)


class TelegramSmsProvider(SmsProvider):
    def __init__(self, token, chat_id, templates):
        super().__init__(templates, "[From Telegram Test]")
        self.api_url = "https://api.telegram.org/bot{}/sendMessage".format(token)
        self.chat_id = chat_id

    def do_send(self, phone: str, content: str):
        post_data = {"chat_id": self.chat_id, "text": content}
        try:
            resp = requests.post(self.api_url, json=post_data, timeout=5)
            _LOGGER.info(
                "send sms by telegram resp: {}".format(resp.status_code, resp.text)
            )
            if resp.status_code != 200:
                raise SendSMSError(
                    "send telegram sms fail because {}".format(resp.text)
                )
        except RequestException as e:
            raise SendSMSError(str(e))
