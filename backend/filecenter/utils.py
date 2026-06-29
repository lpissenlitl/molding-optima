import os
import time
import re
from django.conf import settings
from extensions.exceptions import BizException, ERROR_REQUIRED_FIELD, ERROR_ILLEGAL_ARGUMENT, ERROR_FOLDER_NAME_NOT_ALLOWED
from masterdata.models import Mold
from utils.object_utils import safe_get

# molding-optima 不引入 moldflow/schedule/trial。
# 以下 import 为可选依赖，未启用时 usage_type 仅支持 'mold' 与 'process'。
try:
    from moldflow.models import MoldflowResult
    HAS_MOLDFLOW = True
except ImportError:
    HAS_MOLDFLOW = False

try:
    from schedule.models import MasterSchedule, MoldRequirement, ReadinessChecklist
    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False

try:
    from trial.models import TrialSession
    HAS_TRIAL = True
except ImportError:
    HAS_TRIAL = False


def build_mold_dir(mold: Mold):
    """
    构建模具相关文件存储目录
    根据模具的创建日期，模具编号 生成文件存储目录
    
    Args:
        mold (Mold): 模具对象
    
    Returns:
        str: 相对文件路径
    
    Raises:
        ValueError: 输入参数非法或包含危险字符
    """
    if not mold:
        raise BizException(ERROR_REQUIRED_FIELD, "mold must not be empty")
    create_date = mold.created_at
    if not create_date: 
        raise BizException(ERROR_REQUIRED_FIELD, "mold created_at must not be empty")
    safe_mold_no = sanitize_folder_name(mold.mold_no)
    if not safe_mold_no: 
        raise BizException(ERROR_FOLDER_NAME_NOT_ALLOWED, "mold_no illegal")
    return f"mold_files/{create_date:%Y}/{create_date:%m}/{safe_mold_no}"    
    

def build_storage_path(tenant_slug: str, file_md5: str, ext: str, business_id: str, usage_type: str = "unknown"):
    """
    构建多租户隔离的文件存储绝对路径，并自动创建所需目录。
    
    路径格式：
        {STORE_PATH}/{tenant_slug}/files/{YYYY-MM}/{file_md5}.{ext}
    
    Args:
        tenant_slug (str): 租户唯一标识（如 'tn_xK9m2QzLpR7vNwEa'）
        file_md5 (str): 文件内容的 MD5 哈希（32位小写十六进制）
        ext (str): 文件扩展名（包含字母、数字、下划线，如 'pdf', 'jpg', 'mp4）
        business_id (str): 业务 ID，如 mold_id，补全信息
        usage_type (str): 文件用途，决定存放位置
    
    Returns:
        str: 文件存储的相对路径
        str: 完整的绝对文件路径
    
    Raises:
        ValueError: 输入参数非法或包含危险字符
    """
    # --- 输入校验和清理 ---
    if not tenant_slug or not file_md5 or not ext:
        raise BizException(ERROR_REQUIRED_FIELD, "tenant_slug, file_md5 and ext must not be empty")

    # 1. 校验 tenant_slug：字母、数字、下划线、短横线
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", tenant_slug):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, f"Invalid tenant_slug: {tenant_slug!r}")

    # 2. 校验 file_md5：32位小写十六进制
    if not re.fullmatch(r"[a-f0-9]{32}", file_md5):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, f"Invalid file_md5 (expected 32 hex lowercase): {file_md5!r}")

    # 3. 校验 ext：宽松，包含小写字母、数字、-_
    if not re.fullmatch(r"[a-z0-9_-]+", ext):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, f"Invalid file extension (lowercase letters only): {ext!r}")
    
    # 4. 校验 usage_type：决定文件存储路径
    relative_path = None
    if usage_type == "moldflow":
        if not HAS_MOLDFLOW:
            raise BizException(ERROR_ILLEGAL_ARGUMENT, f"usage_type '{usage_type}' not supported (moldflow module not enabled)")
        moldflow: MoldflowResult = MoldflowResult.objects.filter(id=business_id).first()

        relative_path = f'{build_mold_dir(moldflow.mold)}/moldflow/{file_md5}.{ext}'

    elif usage_type == "self_insp":
        if not HAS_SCHEDULE:
            raise BizException(ERROR_ILLEGAL_ARGUMENT, f"usage_type '{usage_type}' not supported (schedule module not enabled)")
        mold_requirement: MoldRequirement = MoldRequirement.objects.filter(id=business_id).select_related("readiness_checklist", "mold").first()

        # 模具自检分版本
        safe_trial_version = sanitize_folder_name(safe_get(mold_requirement, "readiness_checklist.trial_version"))

        relative_path = f"{build_mold_dir(mold_requirement.mold)}/{safe_trial_version}/{usage_type}/{file_md5}.{ext}"

    elif usage_type in [ "trial_issue", "trial_record" ]:
        if not HAS_TRIAL:
            raise BizException(ERROR_ILLEGAL_ARGUMENT, f"usage_type '{usage_type}' not supported (trial module not enabled)")
        trial_session: TrialSession = TrialSession.objects.filter(id=business_id).select_related("mold").first()
        # 测试问题点分版本
        safe_trial_version = sanitize_folder_name(safe_get(trial_session, "trial_version"))

        relative_path = f"{build_mold_dir(trial_session.mold)}/{safe_trial_version}/{usage_type}/{file_md5}.{ext}"

    elif usage_type == "mold":
        # molding-optima 专用：模具附件
        mold = Mold.objects.filter(id=business_id).first()
        if not mold:
            raise BizException(ERROR_REQUIRED_FIELD, f"mold not found: {business_id}")
        relative_path = f"{build_mold_dir(mold)}/{file_md5}.{ext}"

    elif usage_type == "process":
        # molding-optima 专用：工艺附件（不依赖模具）
        from datetime import datetime
        date_dir = datetime.now().strftime("%Y/%m")
        relative_path = f"process_files/{date_dir}/{business_id}/{file_md5}.{ext}"

    else:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, f"Invalid usage_type: {usage_type!r}")
        
    # --- 构建路径 ---
    full_path = os.path.join(settings.STORE_PATH, tenant_slug, relative_path)

    # --- 确保目录存在 ---
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    return full_path, relative_path


def build_file_path(tenant_slug: str, relative_path: str) -> str:
    """
    构建文件访问 path：
        {STORE_URL}/{tenant_slug}/{relative_path}
    """
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", tenant_slug):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "Invalid tenant_slug")
    
    return f"{settings.STORE_PATH}/{tenant_slug}/{relative_path}"


def build_temp_chunk_dir(tenant_slug: str, finally_md5: str) -> str:
    """
    构建分片临时存储路径：
        {STORE_PATH}/{tenant_slug}/temp/{YYYY-MM}/{finally_md5}
    """
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", tenant_slug):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "Invalid tenant_slug")
    if not re.fullmatch(r"[a-f0-9]{32}", finally_md5):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "Invalid finally_md5")
    
    # --- 构建路径 ---
    date_dir = time.strftime("%Y-%m")
    rel_dir = f"temp/{date_dir}/{finally_md5}"
    full_dir = os.path.join(settings.STORE_PATH, tenant_slug, rel_dir)

    # --- 确保目录存在 ---
    os.makedirs(full_dir, exist_ok=True)

    return full_dir


def sanitize_folder_name(name: str, max_length: int = 50) -> str:
    """
    将任意字符串转换为安全的文件/文件夹名片段
    """
    if not isinstance(name, str):
        name = str(name)
    
    # 1. 去除首尾空白
    name = name.strip()
    
    # 2. 空值处理
    if not name:
        raise BizException(ERROR_FOLDER_NAME_NOT_ALLOWED, "Folder name cannot be empty")
    
    # 3. 移除或替换非法字符（保留字母、数字、中文、下划线、连字符、点）
    # 注意：文件夹名一般不建议用点（.），但可保留
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)  # 替换 Windows 非法字符
    
    # 4. 处理 Windows 保留名（不区分大小写）
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        *(f'COM{i}' for i in range(1, 10)),
        *(f'LPT{i}' for i in range(1, 10))
    }
    if name.upper() in reserved_names:
        name = f"_{name}_"
    
    # 5. 限制长度
    name = name[:max_length].rstrip(' .')  # 避免以空格或点结尾
    
    # 6. 再次检查是否为空
    if not name:
        raise BizException(ERROR_FOLDER_NAME_NOT_ALLOWED, "Folder name invalid")
    
    return name