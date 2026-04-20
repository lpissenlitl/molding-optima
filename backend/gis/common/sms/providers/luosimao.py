import json

import requests

from gis.common.sms.api import SmsProvider, SendSMSError


class LuosimaoSmsProvider(SmsProvider):
    def __init__(self, api_key, sign, host, templates):
        super().__init__(templates, sign, sign_in_front=False)
        self.api_key = api_key
        self.timeout = 5
        self.host = host

    def do_send(self, phone: str, content: str):
        resp = requests.post(
            "{}/v1/send.json".format(self.host),
            auth=("open", "key-{}".format(self.api_key)),
            data={"mobile": phone, "message": content},
            timeout=self.timeout,
            verify=False,
        )
        if resp.status_code != 200:
            raise SendSMSError("luosimao sms fail: {}".format(resp.content))
        result = json.loads(resp.content)
        if result["error"] != 0:
            raise SendSMSError("luosimao sms fail, code: {}".format(result))
