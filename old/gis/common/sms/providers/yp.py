"""
云片短信
https://www.yunpian.com/
"""
import logging

import requests
from yunpian_python_sdk.model import constant as YC
from yunpian_python_sdk.ypclient import YunpianClient

from gis.common.sms.api import SendSMSError, SmsProvider

_LOGGER = logging.getLogger(__name__)


class YPSmsProvider(SmsProvider):
    def __init__(self, api_key, sign, host, templates):
        super().__init__(templates, sign)
        self.clnt = YunpianClient(
            api_key,
            conf={YC.YP_SMS_HOST: host, YC.HTTP_CONN_TIMEOUT: 3, YC.HTTP_SO_TIMEOUT: 5},
        )
        self.sign = sign
        self.host = host

    def do_send(self, phone: str, content: str):
        param = {YC.MOBILE: phone, YC.TEXT: content}
        try:
            r = self.clnt.sms().single_send(param)
        except requests.exceptions.ConnectionError:
            _LOGGER.exception("yp sms url connection fail: {}".format(self.host))
            raise SendSMSError("yp send sms fail cause by proxy connection")
        if not r.is_succ():
            _LOGGER.error(
                "send mobile fail, code: {}, msg: {}, except: {}".format(
                    r.code(), r.msg(), r.exception()
                )
            )
            raise SendSMSError(
                "yp send sms fail, code: {}, msg: {}".format(r.code(), r.msg())
            )
