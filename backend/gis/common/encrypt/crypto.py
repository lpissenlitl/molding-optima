import hashlib

from Crypto.Cipher import AES

BS = 16


def pad(s):
    return s + (BS - len(s) % BS) * chr(BS - len(s) % BS).encode()


def unpad(s):
    return s[0 : -s[-1]]


class AESCipher:
    def __init__(self, key):
        self.key = key

    def encrypt(self, raw):
        raw = pad(raw)
        cipher = AES.new(self.key, AES.MODE_ECB)
        return cipher.encrypt(raw)

    def decrypt(self, enc):
        cipher = AES.new(self.key, AES.MODE_ECB)
        return unpad(cipher.decrypt(enc))


def md5_digest(raw, key=None):
    m = hashlib.md5()
    m.update(raw)
    if key:
        m.update(key)
    return m.digest()
