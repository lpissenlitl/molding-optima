"""
业务错误码与异常定义（统一规范）

错误码格式（6 位）：app_type(1) + module(2) + error_seq(3)
    - app_type: 应用类型（1=Web/API）
    - module:   模块编号（2 位字符串，如 "00"=通用、"01"=认证、"07"=工艺）
    - error_seq: 模块内错误序号（3 位，从 1 开始）

模块编号规划：
    00  通用（系统级错误码）
    01  认证 / 用户
    02  公司
    03  组织
    04  权限
    05  角色
    06  主数据 / Masterdata
    07  工艺 / Process
    08  报表 / Reporting
    09  文件中心 / File Center
    10+ 未来扩展

命名规范：ERROR_<实体>_<场景>
    - 实体：MOLD / MACHINE / POLYMER / PROCESS / USER / ROLE / ...
    - 场景：NOT_FOUND / EXISTED / INVALID / REQUIRED / OUT_OF_RANGE / FAILED / ...

使用规范：
    raise BizException(ERROR_MOLD_NOT_FOUND, f"模具不存在: id={mold_id}")
"""


class BizErrorCode:
    """业务错误码（不可变对象）"""

    # 应用类型常量
    APP_WEB = 1
    APP_WORKER = 2
    APP_MOBILE = 3

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

    def __hash__(self):
        return hash(self.code)

    def __eq__(self, other):
        if not isinstance(other, BizErrorCode):
            return False
        return self.code == other.code

    def __repr__(self):
        return f"BizErrorCode(code={self.code}, message={self.message!r})"

    @classmethod
    def create(
        cls,
        module: str,
        error_seq: int,
        message: str,
        app_type: int = APP_WEB,
    ) -> "BizErrorCode":
        """生成 6 位错误码：app_type(1) + module(2) + error_seq(3)

        Args:
            module: 2 位字符串模块编号（如 "00"=通用、"07"=工艺）
            error_seq: 模块内错误序号（1~999）
            message: 默认错误消息
            app_type: 应用类型（默认 Web/API = 1）

        Returns:
            BizErrorCode 实例

        Example:
            >>> BizErrorCode.create("07", 1, "模具不存在")
            BizErrorCode(code=107001, message='模具不存在')
        """
        if len(module) != 2 or not module.isdigit():
            raise ValueError(f"module 必须是 2 位数字字符串，得到: {module!r}")
        if not (1 <= error_seq <= 999):
            raise ValueError(f"error_seq 必须在 1~999 之间，得到: {error_seq}")
        code = int(f"{app_type}{module}{error_seq:03d}")
        return cls(code, message)


# ============================================================
# 模块编号常量
# ============================================================
MOD_COMMON = "00"   # 通用（系统级错误码）


# ============================================================
# 通用错误码（所有模块复用）
# ============================================================
ERROR_SYSTEM_EXCEPTION  = BizErrorCode.create(MOD_COMMON, 1,   "系统异常，请联系管理员")
ERROR_ILLEGAL_ARGUMENT  = BizErrorCode.create(MOD_COMMON, 2,   "非法参数")
ERROR_REQUIRED_FIELD    = BizErrorCode.create(MOD_COMMON, 3,   "缺少必填字段")
ERROR_DATA_NOT_FOUND    = BizErrorCode.create(MOD_COMMON, 4,   "数据不存在")
ERROR_DATA_FOUND        = BizErrorCode.create(MOD_COMMON, 5,   "数据已存在")
ERROR_DATA_INVALID      = BizErrorCode.create(MOD_COMMON, 6,   "数据无效")
ERROR_OPERATION_FAILED  = BizErrorCode.create(MOD_COMMON, 7,   "操作失败")
ERROR_ACCESS_DENIED     = BizErrorCode.create(MOD_COMMON, 8,   "访问受限")
ERROR_UPLOAD_FILE_FAILED = BizErrorCode.create(MOD_COMMON, 9,   "上传文件失败")

# 兼容旧名：ERROR_ACCESS_LIMIT 是历史命名（曾被 process.rule_service 引用），与
# ERROR_ACCESS_DENIED 语义一致（“权限受限 / 操作被限”）。保留别名以免破坏存量代码。
ERROR_ACCESS_LIMIT      = ERROR_ACCESS_DENIED


class BizException(Exception):
    """业务异常（所有业务异常都应抛出此类型）

    使用规范：
        raise BizException(ERROR_DATA_NOT_FOUND, "用户不存在: id=123")

    错误消息格式："{默认消息} - {调用方补充的 message}"
    """

    def __init__(self, code: BizErrorCode, message: str = ""):
        if not isinstance(code, BizErrorCode):
            raise TypeError(
                f"BizException 第一个参数必须是 BizErrorCode 实例，得到: {type(code).__name__}"
            )
        if message and not isinstance(message, str):
            message = str(message)

        _msg = code.message
        if message:
            _msg = "{} - {}".format(code.message, message)
        self.code = code.code
        self.error_code = code  # 完整 BizErrorCode（方便反查默认消息）
        self.detail_message = _msg

        super().__init__(f"code: {code.code}, message: {_msg}")

    def __str__(self):
        return self.detail_message
