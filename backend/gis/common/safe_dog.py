"""
Open API Client SDK
"""
import hmac
import json
import logging
from collections import OrderedDict
from hashlib import sha1

import requests

from gis.common.conf.api import conf_decorator


class SafeDogClient:
    def __init__(self, api_domain, app_key, app_secret, use_https=False):
        logging.info(
            "safe dog init {}{}{}{}".format(api_domain, app_key, app_secret, use_https)
        )

        self.api_domain = api_domain
        self.app_key = app_key
        self.app_secret = app_secret
        self.http_domain = ("https://" if use_https else "http://") + api_domain + "/"

    def verify_token(self, user_id, token, ip):
        data = {"app_key": self.app_key, "user_id": user_id, "token": token, "ip": ip}
        sorted_data = json.dumps(OrderedDict(sorted(data.items())))
        sign = self._encrypt_data(sorted_data)
        data["sign"] = sign

        return self._request("verify_token", data)

    def _request(self, uri, data):
        logging.info("request:{} {} - {}".format(self.http_domain, uri, data))
        resp = requests.post(self.http_domain + uri, data=data)
        logging.info("response text: {}".format(resp.text))

        if resp.status_code != 200:
            return False
        resp_json = json.loads(resp.content)
        return resp_json["status"] == 0

    def _encrypt_data(self, data):
        return hmac.new(
            self.app_secret.encode(), data.encode("utf-8"), sha1
        ).hexdigest()


@conf_decorator("safe_dog_conf.json")
class SafeDogConf:
    api_domain = "1111"
    app_key = "111"
    app_secret = "111"
    use_https = False


if SafeDogConf.api_domain:
    client = SafeDogClient(
        SafeDogConf.api_domain,
        SafeDogConf.app_key,
        SafeDogConf.app_secret,
        SafeDogConf.use_https,
    )
else:
    logging.info("project has no safe config")
