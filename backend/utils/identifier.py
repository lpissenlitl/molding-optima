"""
业务 code 自动生成工具

设计原则：
- 中文 → 拼音（pypinyin），英文部分保留并转小写
- 自动剥离"公司级"后缀（"股份有限公司"、"集团"、"公司" 等）
- 不剥离"组织级"后缀（"车间"、"部门"、"工段" 等），因为组织本身可能是车间
- 中文限制在 6 字以内，避免超长
- 冲突时自动加数字后缀（xxx_2、xxx_3...）

Usage:
    from utils.identifier import auto_code_from_name, ensure_unique_code

    # 自动生成 code（基于 name）
    code = auto_code_from_name("海信模具股份有限公司")  # → "hai_xin_mu_ju"

    # 冲突加后缀
    def exists(c):
        return Company.objects.filter(code=c).exists()
    code = ensure_unique_code("hai_xin_mu_ju", exists)
    # → "hai_xin_mu_ju_2"（如果已存在）
"""
import re
from django.utils.text import slugify


# 公司级后缀（适用于 Company）
COMPANY_SUFFIXES = [
    '股份有限公司',
    '有限责任公司',
    '集团有限公司',
    '有限公司',
    '集团',
    '分公司',
    '子公司',
    'Co.,Ltd',
    'Co. Ltd',
    'Inc.',
    'Ltd.',
    'Corp.',
    '公司',
    '厂',
]

# 组织级后缀（适用于 Organization）
ORGANIZATION_SUFFIXES = [
    '事业部',
    '部门',
    '车间',
    '工段',
    '班组',
    '部',
]

# 中文名最大字符数
MAX_NAME_CHARS = 6


def auto_code_from_name(
    name: str,
    max_length: int = 30,
    suffixes = COMPANY_SUFFIXES,
):
    """
    基于实体名称自动生成业务 code（短而可读）

    Args:
        name: 实体名称
        max_length: code 最大长度
        suffixes: 要剥离的后缀列表，默认是公司级后缀

    Returns:
        标准化后的 code（小写、下划线连接），name 为空时返回 None

    Examples:
        >>> auto_code_from_name("海信模具股份有限公司")
        'hai_xin_mu_ju'

        >>> auto_code_from_name("装配车间", suffixes=ORGANIZATION_SUFFIXES)
        'zhuang_pei'

        >>> auto_code_from_name("Engineering Team")
        'engineering_team'

        >>> auto_code_from_name("海信 Mold Co.")
        'hai_xin_mold_co'

        >>> auto_code_from_name("")
        None
    """
    if not name or not name.strip():
        return None

    name = name.strip()

    # 1. 去掉指定后缀（按列表顺序，先长后短）
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
            break

    # 2. 限制中文字符数（仅限中文，保留英文不动）
    cn_count = sum(1 for c in name if '\u4e00' <= c <= '\u9fff')
    if cn_count > MAX_NAME_CHARS:
        kept, kept_cn = [], 0
        for c in name:
            if '\u4e00' <= c <= '\u9fff':
                if kept_cn >= MAX_NAME_CHARS:
                    continue
                kept_cn += 1
            kept.append(c)
        name = ''.join(kept).strip()

    # 3. 转拼音
    try:
        from pypinyin import lazy_pinyin
        parts = lazy_pinyin(name)
        code = _join_pinyin_parts(parts)
    except ImportError:
        code = slugify(name).replace('-', '_')

    # 4. 清理：只保留小写字母、数字、下划线
    code = re.sub(r'[^a-z0-9_]+', '', code.lower())
    code = re.sub(r'_+', '_', code).strip('_')

    return code[:max_length] or None


def _join_pinyin_parts(parts: list) -> str:
    """
    拼接 pinyin parts，处理英文串内部空格

    pypinyin lazy_pinyin 行为：
    - 中文：按字拆分 ['hai', 'xin']
    - 英文：作为整体保留 ['Engineering Team']
    - 中英混合：['hai', 'xin', ' Mold']

    这里把英文串内部空格也拆开，作为独立 token。
    """
    expanded = []
    for part in parts:
        if not part:
            continue
        if re.search(r'[a-zA-Z]', part):
            # 英文串：按空格、连字符拆成多个 token
            sub_parts = re.split(r'[\s\-]+', part.strip())
            expanded.extend(p.lower() for p in sub_parts if p)
        else:
            expanded.append(part)
    return '_'.join(expanded)


def normalize_code(code: str) -> str:
    """
    标准化用户手动输入的 code（保留原意，最小化清洗）

    Examples:
        >>> normalize_code("Hisense Mold")
        'hisense_mold'

        >>> normalize_code("  ZP-1  ")
        'zp_1'

        >>> normalize_code("ZP.2")
        'zp_2'
    """
    if not code:
        return ''
    code = re.sub(r'[\s\-]+', '_', code.strip().lower())
    code = re.sub(r'[^a-z0-9_]+', '', code)
    code = re.sub(r'_+', '_', code).strip('_')
    return code


def ensure_unique_code(
    base_code: str,
    exists_check,
    max_attempts: int = 999,
) -> str:
    """
    如果 code 冲突，自动加数字后缀

    Args:
        base_code: 基础 code（如 "hai_xin_mu_ju"）
        exists_check: 检查 code 是否存在的 callable，接收 code 参数，返回 bool
        max_attempts: 最大尝试次数

    Examples:
        >>> ensure_unique_code("hai_xin", lambda c: c == "hai_xin")
        'hai_xin_2'

        >>> ensure_unique_code(
        ...     "hai_xin",
        ...     lambda c: c in ("hai_xin", "hai_xin_2")
        ... )
        'hai_xin_3'
    """
    if not base_code:
        return ''

    code = base_code
    if not exists_check(code):
        return code

    for i in range(2, max_attempts + 1):
        code = f"{base_code}_{i}"
        if not exists_check(code):
            return code

    raise ValueError(f"无法生成唯一 code，base={base_code}")