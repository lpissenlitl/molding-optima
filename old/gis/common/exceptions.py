class BizErrorCode:
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __hash__(self):
        return self.code

    def __eq__(self, other):
        if not isinstance(other, BizErrorCode):
            return False
        return other.code == self.code


# 预定义常见错误类型
ERROR_ILLEGAL_PARAMETER = BizErrorCode(1, "params illegal")
ERROR_ACCESS_LIMIT = BizErrorCode(2, "limited access")


class BizException(Exception):
    def __init__(self, error_code, message=None):
        if message and not isinstance(message, str):
            message = str(message)
        if isinstance(error_code, int):
            error_code = BizErrorCode(error_code, message)
        assert isinstance(error_code, BizErrorCode)
        print(f"错误信息{error_code}")
        self.error_code = error_code
        _msg = error_code.message
        if message:
            _msg = "{} - {}".format(error_code.message, message)
        self.detail_message = _msg
        super().__init__("code: {}, message: {}".format(error_code.code, _msg))


class IllegalRequestException(Exception):
    pass
