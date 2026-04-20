from django.test import TestCase

from gis.common.sms.client import SmsClient


class SmsClientTestCase(TestCase):
    def test_send_sms(self):
        client = SmsClient()
        client.send("15608796849", "123456")
