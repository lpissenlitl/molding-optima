"""
DDM 数据同步服务

从 DDM（Design Data Management）系统获取模具数据并同步到本地数据库
"""
import re
import pyodbc
from django.db import transaction
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


# ============================================================
# SQL Server 连接配置
# ============================================================

def get_sql_server_driver():
    """获取可用的 SQL Server ODBC 驱动"""
    drivers = pyodbc.drivers()
    patterns = [
        r'ODBC Driver \d+ for SQL Server',
        r'SQL Server Native Client \d+\.\d+',
        r'SQL Server'
    ]
    for pat in patterns:
        for d in drivers:
            if re.search(pat, d, re.IGNORECASE):
                return d
    raise RuntimeError("未找到可用的 SQL Server ODBC 驱动")


def fetch_ddm_mold_data():
    """从 DDM 系统获取模具数据"""
    driver = get_sql_server_driver()
    driver = getattr(settings, 'SQL_SERVER_DRIVER', driver)
    server_ip = getattr(settings, 'SQL_SERVER_IP', "172.16.126.217")
    username = getattr(settings, 'SQL_SERVER_USER', "md")
    password = getattr(settings, 'SQL_SERVER_PASSWORD', "md123")
    database = getattr(settings, 'SQL_SERVER_DATABASE', "MoldDesign_DATA")
    tablename = getattr(settings, 'SQL_SERVER_TABLE', "[MoldDesign_DATA].[sy].[式样书_提取到模鼎的临时表]")
    
    conn_str = (
        f'DRIVER={{{driver}}};'
        f'SERVER={server_ip};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password}'
    )
    query = """
    SELECT
        [模号],
        [提取时间],
        [浇口形式],
        [冷却加热方式_型芯],
        [顶出复位],
        [海信顶出孔直径及位置],
        [顶出距离],
        [产品图号],
        [产品名称],
        [注射形式],
        [取件方式],
        [是否为多色产品],
        [模具类型],
        [阀针控制方式],
        [本厂注塑机],
        [热嘴点数],
        [热流道品牌],
        [冷却加热方式_型腔],
        [模腔数],
        [模具强回位及牙型],
        [喷嘴SR_直径_模具],
        [热流道形式],
        [客户注塑机]
    FROM {tablename}
    """.format(tablename=tablename)

    try:
        conn = pyodbc.connect(conn_str, timeout=30)
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        result = [dict(zip(columns, row)) for row in rows]
        cursor.close()
        conn.close()
        return result
    except pyodbc.Error as e:
        print(e)
        return []


# ============================================================
# 数据解析辅助函数
# ============================================================

def _parse_shot_count(value):
    """
    解析是否为多色产品，转换为 shot_count（注射次数）：
    - '是', 'True', 'true', '1', 'yes' -> 2（双色/多色）
    - '否', 'False', 'false', '0', 'no', '单色', '不需要' -> 1（单色）
    - 其他情况默认为 1
    """
    if value is None:
        return None
    
    value_str = str(value).strip().lower()
    
    if value_str in ['是', 'true', '1', 'yes', '双色', '多色']:
        return 2
    
    if value_str in ['否', 'false', '0', 'no', '单色', '不需要', '']:
        return 1
    
    return 1


def _parse_hot_nozzle_count(value):
    """
    解析热嘴点数，支持多种格式：
    - 纯数字：'4', '18' -> 返回整数
    - 加法格式：'18+2', '3+4+2' -> 返回总和
    - 带文字：'6点', '1点' -> 提取数字
    - 混合格式：'硬胶：2，软胶：2' -> 提取所有数字并求和
    """
    if value is None:
        return None
    
    value_str = str(value).strip()
    if not value_str or value_str in ['/', '无', '0']:
        return None
    
    numbers = re.findall(r'\d+', value_str)
    if not numbers:
        return None
    
    total = sum(int(n) for n in numbers)
    return total if total > 0 else None


def _parse_ejection_stroke(value):
    """
    解析顶出距离，支持多种格式：
    - '80mm', '90', '130mm' -> 提取数字
    - '80mm；加速顶' -> 提取第一个数字
    - '顶出距分别为30mm、40mm' -> 提取第一个数字
    """
    if value is None:
        return None
    
    value_str = str(value).strip()
    if not value_str or value_str in ['/', '无', '按需要', '按需要设计']:
        return None
    
    match = re.search(r'(\d+(?:\.\d+)?)', value_str)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    
    return None


def _parse_ejector_hole_info(value):
    """
    解析海信顶出孔直径及位置信息
    格式示例：'150*700，φ58' 或 '100*400，φ38'
    返回字典：{'ejector_rod_hole_spacing_x': 150, 'ejector_rod_hole_spacing_y': 700, 'ejector_rod_hole_diameter': 58}
    """
    if value is None:
        return None
    
    value_str = str(value).strip()
    if not value_str or value_str in ['/', '无', 'None']:
        return None
    
    result = {}
    
    # 尝试匹配格式：数字*数字，φ数字
    pattern = r'(\d+(?:\.\d+)?)\s*[\*×xX]\s*(\d+(?:\.\d+)?)\s*[,，]\s*[φΦ]?\s*(\d+(?:\.\d+)?)'
    match = re.search(pattern, value_str)
    
    if match:
        try:
            result['ejector_rod_hole_spacing_x'] = float(match.group(1))
            result['ejector_rod_hole_spacing_y'] = float(match.group(2))
            result['ejector_rod_hole_diameter'] = float(match.group(3))
        except ValueError:
            pass
    else:
        # 尝试只提取直径
        dia_match = re.search(r'[φΦ]\s*(\d+(?:\.\d+)?)', value_str)
        if dia_match:
            try:
                result['ejector_rod_hole_diameter'] = float(dia_match.group(1))
            except ValueError:
                pass
    
    return result if result else None


def _parse_nozzle_info(value):
    """
    解析喷嘴 SR_直径_模具信息，提取 SR 值
    例如：'SR21/φ8', 'SR40/φ13', 'SR 23  /   φ5'
    返回：SR 值的浮点数
    """
    if value is None:
        return None
    
    value_str = str(value).strip()
    if not value_str or value_str in ['/', '无']:
        return None
    
    sr_match = re.search(r'SR\s*(\d+(?:\.\d+)?)', value_str, re.IGNORECASE)
    if sr_match:
        try:
            return float(sr_match.group(1))
        except ValueError:
            pass
    
    return None


def _parse_recommended_tonnage(value):
    """
    解析客户注塑机信息，提取吨位
    支持格式：'4000T', 'HTF470T', '650T', 'SM3200T', 'T4000', 'T650' 等
    返回：吨位的整数
    """
    if value is None:
        return None
    
    value_str = str(value).strip()
    if not value_str or value_str in ['/', '无', 'None']:
        return None
    
    # 尝试匹配 xxxT 格式（数字在前，T在后）
    match = re.search(r'(\d+)\s*T', value_str, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    
    # 尝试匹配 Txxx 格式（T在前，数字在后）
    match = re.search(r'T\s*(\d+)', value_str, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    
    return None


# ============================================================
# DDM 字段映射配置
# ============================================================

DDM_MOLD_FIELD_MAPPING = {
    # 1. 模号 - Mold.mold_no
    '模号': ('mold_no', str),
    
    # 2. 提取时间 - 数据提取时间戳，业务上不需要存储
    # '提取时间': None,
    
    # 3. 浇口形式 - Gate.gate_type（浇口类型）
    '浇口形式': ('gate.gate_type', str),
    
    # 4. 冷却加热方式_型芯 - CoolingSystem.cooling_core_type
    '冷却加热方式_型芯': ('cooling_system.cooling_core_type', str),
    
    # 5. 顶出复位 -  EjectionSystem.ejection_type
    '顶出复位': ('ejection_system.ejection_type', str),
    
    # 6. 海信顶出孔直径及位置 - EjectionSystem（解析为三个字段）
    '海信顶出孔直径及位置': ('ejection_system.ejector_hole_info', _parse_ejector_hole_info),
    
    # 7. 顶出距离 - EjectionSystem.ejection_stroke
    '顶出距离': ('ejection_system.ejection_stroke', _parse_ejection_stroke),
    
    # 8. 产品图号 - Cavity.product_code（通过GatingSystem关联）
    '产品图号': ('cavity.product_code', str),
    
    # 9. 产品名称 - Cavity.product_name
    '产品名称': ('cavity.product_name', str),
    
    # 10. 注射形式 - GatingSystem.runner_type（流道类型）
    '注射形式': ('gating_system.runner_type', str),
    
    # 11. 取件方式 - Mold.part_removal_action
    '取件方式': ('part_removal_action', str),
    
    # 12. 是否为多色产品 - Mold.shot_count（单色=1，双色/多色=2）
    '是否为多色产品': ('shot_count', _parse_shot_count),
    
    # 13. 模具类型 - Mold.structure（模具结构：两板模、三板模等）
    '模具类型': ('structure', str),
    
    # 14. 阀针控制方式 - GatingSystem.valve_actuation_type
    '阀针控制方式': ('gating_system.valve_actuation_type', str),
    
    # 15. 本厂注塑机 - 外部参考信息，不存储到数据库
    # '本厂注塑机': None,
    
    # 16. 热嘴点数 - GatingSystem.hot_runner_nozzle_count
    '热嘴点数': ('gating_system.hot_runner_nozzle_count', _parse_hot_nozzle_count),
    
    # 17. 热流道品牌 - GatingSystem.hot_runner_supplier
    '热流道品牌': ('gating_system.hot_runner_supplier', str),
    
    # 18. 冷却加热方式_型腔 - CoolingSystem.cooling_cavity_type
    '冷却加热方式_型腔': ('cooling_system.cooling_cavity_type', str),
    
    # 19. 模腔数 - Mold.cavity_layout（模腔布局：如1+1, 1*2等）
    '模腔数': ('cavity_layout', str),
    
    # 20. 模具强回位及牙型 - EjectionSystem.reset_method（复位方式）
    '模具强回位及牙型': ('ejection_system.reset_method', str),
    
    # 21. 喷嘴SR_直径_模具 - GatingSystem.sprue_bushing_radius
    '喷嘴SR_直径_模具': ('gating_system.sprue_bushing_radius', _parse_nozzle_info),
    
    # 22. 热流道形式 - GatingSystem.hot_runner_system_type（如果与注射形式不同则覆盖）
    '热流道形式': ('gating_system.hot_runner_system_type', str),
    
    # 23. 客户注塑机 - Mold.recommended_tonnage（推荐注塑机吨位）
    '客户注塑机': ('recommended_tonnage', _parse_recommended_tonnage),
}


# ============================================================
# 主同步函数
# ============================================================

def sync_molds_from_ddm():
    """
    从 DDM 系统获取模具数据并更新到本地 Mold 表及关联表
    根据模号(mold_no)匹配，存在则更新，不存在则跳过
    更新的表包括：Mold, GatingSystem, CoolingSystem, EjectionSystem
    """
    from masterdata.models import Mold, GatingSystem, CoolingSystem, EjectionSystem, Cavity, Gate
    
    ddm_mold_data = fetch_ddm_mold_data()
    
    if not ddm_mold_data:
        logger.warning('未从DDM系统获取到模具数据')
        return
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for ddm_record in ddm_mold_data:
        try:
            # 获取模号
            mold_no = ddm_record.get('模号')
            if not mold_no:
                logger.warning(f'记录缺少模号，跳过: {ddm_record}')
                skipped_count += 1
                continue
            
            # 查找对应的模具记录
            try:
                mold = Mold.objects.get(mold_no=mold_no)
            except Mold.DoesNotExist:
                logger.info(f'模具编号 {mold_no} 在本地不存在，跳过')
                skipped_count += 1
                continue
            
            # 分类收集更新字段
            mold_update_fields = {}
            gating_system_fields = {}
            cooling_system_fields = {}
            ejection_system_fields = {}
            gate_fields = {}
            cavity_fields = {}  # Cavity字段
            
            for ddm_field, (model_field, converter) in DDM_MOLD_FIELD_MAPPING.items():
                if model_field == 'mold_no':
                    continue
                
                ddm_value = ddm_record.get(ddm_field)
                
                if ddm_value is None or (isinstance(ddm_value, str) and not ddm_value.strip()):
                    continue
                
                try:
                    if callable(converter):
                        converted_value = converter(ddm_value)
                    else:
                        converted_value = converter(ddm_value)
                    
                    if converted_value is not None:
                        if model_field.startswith('gating_system.'):
                            gating_field = model_field.replace('gating_system.', '')
                            gating_system_fields[gating_field] = converted_value
                        elif model_field.startswith('cooling_system.'):
                            cooling_field = model_field.replace('cooling_system.', '')
                            cooling_system_fields[cooling_field] = converted_value
                        elif model_field.startswith('ejection_system.'):
                            ejection_field = model_field.replace('ejection_system.', '')
                            if ejection_field == 'ejector_hole_info' and isinstance(converted_value, dict):
                                ejection_system_fields.update(converted_value)
                            else:
                                ejection_system_fields[ejection_field] = converted_value
                        elif model_field.startswith('gate.'):
                            gate_field = model_field.replace('gate.', '')
                            gate_fields[gate_field] = converted_value
                        elif model_field.startswith('cavity.'):
                            cavity_field = model_field.replace('cavity.', '')
                            cavity_fields[cavity_field] = converted_value
                        else:
                            mold_update_fields[model_field] = converted_value
                            
                except (ValueError, TypeError) as e:
                    logger.warning(f'字段 {ddm_field} 转换失败: {ddm_value}, 错误: {e}')
                    continue
            
            # 使用事务确保数据一致性
            with transaction.atomic():
                # 1. 更新 Mold 主表
                if mold_update_fields:
                    Mold.objects.filter(id=mold.id).update(**mold_update_fields)
                    logger.debug(f'更新 Mold: {list(mold_update_fields.keys())}')
                
                # 2. 更新或创建 GatingSystem（一对多：遍历所有关联记录）
                if gating_system_fields:
                    gating_systems = GatingSystem.objects.filter(mold=mold)
                    if gating_systems.exists():
                        # 更新所有现有的 GatingSystem 记录
                        updated_count_gs = gating_systems.update(**gating_system_fields)
                        logger.debug(f'更新 {updated_count_gs} 条 GatingSystem: {list(gating_system_fields.keys())}')
                    else:
                        # 如果没有现有记录，则创建一条
                        GatingSystem.objects.create(mold=mold, **gating_system_fields)
                        logger.debug(f'创建 GatingSystem: {list(gating_system_fields.keys())}')
                
                # 3. 更新或创建 CoolingSystem（一对一）
                if cooling_system_fields:
                    cooling_obj, created = CoolingSystem.objects.update_or_create(
                        mold=mold,
                        defaults=cooling_system_fields
                    )
                    action = '创建' if created else '更新'
                    logger.debug(f'{action} CoolingSystem: {list(cooling_system_fields.keys())}')
                
                # 4. 更新或创建 EjectionSystem（一对一）
                if ejection_system_fields:
                    ejection_obj, created = EjectionSystem.objects.update_or_create(
                        mold=mold,
                        defaults=ejection_system_fields
                    )
                    action = '创建' if created else '更新'
                    logger.debug(f'{action} EjectionSystem: {list(ejection_system_fields.keys())}')
                
                # 5. 更新 Cavity（一对多：对每个GatingSystem下的所有Cavity更新）
                if cavity_fields:
                    gating_systems = GatingSystem.objects.filter(mold=mold)
                    total_cavity_updated = 0
                    for gating_obj in gating_systems:
                        cavities = Cavity.objects.filter(gating_system=gating_obj)
                        if cavities.exists():
                            # 更新该GatingSystem下的所有Cavity
                            updated_count_c = cavities.update(**cavity_fields)
                            total_cavity_updated += updated_count_c
                        else:
                            # 如果没有现有Cavity，创建一个
                            Cavity.objects.create(
                                gating_system=gating_obj,
                                product_name=mold.product_description or '',
                                **cavity_fields
                            )
                            total_cavity_updated += 1
                    logger.debug(f'更新/创建 {total_cavity_updated} 条 Cavity: {list(cavity_fields.keys())}')
                
                # 6. 更新 Gate（一对多：对每个Cavity下的所有Gate更新）
                if gate_fields:
                    total_gate_updated = 0
                    # 遍历所有GatingSystem
                    gating_systems = GatingSystem.objects.filter(mold=mold)
                    for gating_obj in gating_systems:
                        # 遍历该GatingSystem下的所有Cavity
                        cavities = Cavity.objects.filter(gating_system=gating_obj)
                        for cavity in cavities:
                            gates = Gate.objects.filter(cavity=cavity)
                            if gates.exists():
                                # 更新该Cavity下的所有Gate
                                updated_count_g = gates.update(**gate_fields)
                                total_gate_updated += updated_count_g
                            else:
                                # 如果没有现有Gate，创建一个
                                Gate.objects.create(cavity=cavity, **gate_fields)
                                total_gate_updated += 1
                    logger.debug(f'更新/创建 {total_gate_updated} 条 Gate: {list(gate_fields.keys())}')
            
            updated_count += 1
            logger.info(f'成功更新模具 {mold_no}')
                
        except Exception as e:
            error_count += 1
            logger.error(f'处理模具记录时出错: {ddm_record}, 错误: {str(e)}', exc_info=True)
            continue
    
    logger.info(f'DDM模具数据同步完成: 更新{updated_count}条, 跳过{skipped_count}条, 错误{error_count}条')
    return {
        'updated': updated_count,
        'skipped': skipped_count,
        'errors': error_count
    }
