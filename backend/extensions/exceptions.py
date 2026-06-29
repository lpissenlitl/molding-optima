
class BizErrorCode:
    """业务错误码"""

    # 应用类型常量
    APP_WEB = 1
    APP_WORKER = 2
    APP_MOBILE = 3

    def __init__(self, code, message):
        self.code = code
        self.message = message
        
    def __hash__(self):
        return hash(self.code)
    
    def __eq__(self, other):
        if not isinstance(other, BizErrorCode):
            return False
        return self.code == other.code
    
    # =============================
    # 工具函数：生成完整错误码
    # =============================
    @classmethod
    def create(cls, mod: str, num: int, message:str, app_type: int = APP_WEB, ) -> 'BizErrorCode':
        """生成 6 位错误码：1 + mod + num（3 位）"""
        code = int(f"{app_type}{mod}{num:03d}")
        return cls(code, message)

# 预定义常见错误类型
ERROR_SYSTEM_EXCEPTION = BizErrorCode(10000, "系统异常，请联系管理员")
ERROR_ILLEGAL_ARGUMENT = BizErrorCode(10001, "非法参数")
ERROR_ACCESS_LIMIT = BizErrorCode(10002, "访问限制")
ERROR_REQUIRED_FIELD = BizErrorCode(10003, "缺少必填字段")
ERROR_DATA_NOT_FOUND = BizErrorCode(10004, "数据不存在")
ERROR_DATA_FOUND = BizErrorCode(10005, "数据已存在")
ERROR_UPLOAD_FILE_FAILED = BizErrorCode(10006, "上传文件失败")
ERROR_FOLDER_NAME_NOT_ALLOWED = BizErrorCode(10007, "文件夹名称不允许")
ERROR_TEMPLATE_NOT_FOUND = BizErrorCode(10008, "模板不存在")

class BizException(Exception):
    """业务异常"""
    def __init__(self, code, message: str = ""):
        if message and not isinstance(message, str):
            message = str(message)
        if isinstance(code, int):
            code = BizErrorCode(code, message)
        # print(type(code))
        assert isinstance(code, BizErrorCode)

        _msg = code.message
        if message:
            _msg = "{} - {}".format(code.message, message)
        self.code = code.code
        self.detail_message = _msg

        super().__init__(f"code: {code.code}, message: {_msg}")

    def __str__(self):
        return self.detail_message


class IllegalRequestException(Exception):
    pass