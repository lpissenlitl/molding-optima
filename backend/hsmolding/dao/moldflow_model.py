from gis.common.django_ext.mongo_dao import BaseDoc
from mongoengine import (
    EmbeddedDocument,
    StringField,
    IntField,
    DecimalField,
    ListField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
)


class TableDataItemDoc(EmbeddedDocument):
    label = StringField(null=True)
    unit = StringField(null=True)
    sections = ListField(null=True)


class ProcessMonitorDoc(EmbeddedDocument):
    injection_time = DecimalField(null=True)
    cooling_time = DecimalField(null=True)
    holding_time = DecimalField(null=True)
    mold_opening_time = DecimalField(null=True)
    mold_clamping_time = DecimalField(null=True)

    # mold_open_clamp_time = DecimalField(null=True)  # 开合模时间
    cycle_time = DecimalField(null=True)  #周期时间
    product_projected_area = DecimalField(null=True)
    single_volume = DecimalField(null=True)

    melt_temp = DecimalField(null=True)
    cavity_temp = DecimalField(null=True)
    core_temp = DecimalField(null=True)

    injection_pressure = DecimalField(null=True)
    max_clamping_force = DecimalField(null=True)

    polymer_trademark = StringField(null=True)  # 材料牌号
    thickness = DecimalField(null=True)  # 壁厚
    product_weight = DecimalField(null=True)  # 克重
    gate_temperature = DecimalField(null=True)  # 浇口温度
    pentroof_temperature = DecimalField(null=True)  # 斜顶温度
    slug_temperature = DecimalField(null=True)  # 弹块滑块温度
    lifters_temperature = DecimalField(null=True)  # 内抽温度

    injection = DecimalField(null=True)  # 注塑机压力
    hot_runner_pressure = DecimalField(null=True)  # 热流道压力
    gate_pressure = DecimalField(null=True)  # 浇口压力

    inject_para = EmbeddedDocumentListField(TableDataItemDoc)
    holding_para = EmbeddedDocumentListField(TableDataItemDoc)


# 模流数据
class MoldFlowDoc(BaseDoc):
    project_id = IntField()  # 模号ID
    mold_no = StringField(null=True)
    doc_link = StringField(null=True)  # txt文件
    pdf_link = StringField(null=True)  # pdf文件
    ppt_link = StringField(null=True)  # ppt文件
    monitor_item = EmbeddedDocumentField(ProcessMonitorDoc)
