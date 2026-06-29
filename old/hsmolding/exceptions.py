from gis.common.exceptions import BizErrorCode


ERROR_DATA_EXIST = BizErrorCode(10000, "数据已存在")
ERROR_DATA_NOT_EXIST = BizErrorCode(10001, "数据不存在")
ERROR_PARAM_ERROR = BizErrorCode(10002, "参数错误")
ERROR_TRY_LATER = BizErrorCode(10003, "生成报告错误")

ERROR_INPUT_IS_NULL = BizErrorCode(20000, "提示")  # 前端传值为空，需要填写相应字段

ERROR_PAGE_INFO_NOT_EXISTS = BizErrorCode(30051, "无法识别页面")

ERROR_permission_INFO_NOT_EXISTS = BizErrorCode(30061, "没有操作权限")

ERROR_DATA_STRUCTURE = BizErrorCode(40001, "请检查数据格式")

ERROR_NO_FILE = BizErrorCode(50001, "没有文件")
ERROR_ERROR_FILE_TYPE = BizErrorCode(50002, "请上传约定格式的moldflow txt")
ERROR_FILE_TYPE = BizErrorCode(50003, "请上传图片或pdf格式或ppt格式的文件")
ERROR_TEMPLATE = BizErrorCode(50004, "请使用导出获得正确的模板进行导入")

ERROR_MOLD_NO = BizErrorCode(60001, "模号无效")

ERROR_MACHINE = BizErrorCode(70001, "机器信息不完整")
ERROR_POLYMER = BizErrorCode(70002, "材料信息不完整")
ERROR_PRODUCT = BizErrorCode(70003, "制品信息不完整")

ERROR_COM_TRANSFER = BizErrorCode(80001, "数据传输错误")

ERROR_RULE_ERROR = BizErrorCode(90001, "请检查语法错误")
ERROR_EXPERT_ERROR = BizErrorCode(90002, "专家记录请求错误")