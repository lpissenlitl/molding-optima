

# --- 模具相关信息 ---
MOLD_TYPE_CHOICES = [
    ('injection', '注塑模具'),
    ('stamping', '冲压模具'),
]

MOLD_CATEGORY_CHOICES = [
    ('automotive', '汽车'),
    ('home_appliance', '家电'),
    ('medical', '医疗'),
    ('consumer_electronics', '消费电子'),
    ('packaging', '包装'),
    ('industrial_component', '工业零部件'),
    ('connector', '连接器/接插件'),
    ('optical_lens', '光学镜片'),
    ('daily_necessities', '日用品'),
    ('others', '其他'),
]

MOLD_STRUCTURE_CHOICES = [
    ('two_plate', '两板模'),
    ('three_plate', '三板模'),
    ('hot_runner', '热流道模'),
    ('cold_runner', '冷流道模'),
    ('stack_mold', '叠层模'),
    ('family_mold', '家族模'),
    ('insert_mold', '镶件模'),
    ('unscrewing_mold', '脱螺纹模'),
    ('gas_assist', '气体辅助成型模'),
    ('others', '其他'),
]

MOLD_SHOT_TYPE_CHOICES = [
    ('single', '单次成型'),
    ('multiple', '多次成型'),
]

MOLD_MECHANISM_CHOICES = [
    ('none', '无'),
    ('slide_core', '滑块'),
    ('lift_core', '斜顶'),
    ('rotary_table', '转盘式'),
    ('rotary_core', '转轴式'),
    ('hydraulic_cylinder', '油缸抽芯'),
    ('motor_driven', '电机驱动'),
]

MOLD_SPECIAL_PROCESS_CHOICES = [
    ('gas_assist', '气体辅助'),
    ('insert_molding', '嵌件成型'),
    ('foam', '发泡成型'),
    ('overmolding', '包胶成型'),
    ('pressure', '加压'),
    ('nitrogen', '氮气注射'),
    ('delay', '延时'),
    ('pressure_delay', '加压延时'),
    ('nitrogen_delay', '氮气延时'),
]

MOLD_COOLING_TYPE = [
    ('none', '无冷却'),
    ('conventional', '传统钻孔式'),
    ('conformal', '随形冷却'),
    ('hybrid', '混合式'),
    ('bubbler_spray', '喷流/喷管式'),
    ('thermal_siphon', '热虹吸'),
]

PART_REMOVAL_ACTION_CHOICES = [
    ('manual', '手工取件'),
    ('robot', '机械手取件'),
    ('drop', '自动掉落'),
]

MOLD_COOLING_LAYOUT = [
    ('single_pass', '单程直通'),
    ('multi_pass', '多程U型'),
    ('cascade', '层叠式'),
    ('parallel', '并联'),
    ('series', '串联'),
]

MOLD_COOLING_FITTING_TYPE = [
    ('din7665_m14x1.5', 'DIN 7665 M14×1.5'),
    ('din7665_m16x1.5', 'DIN 7665 M16×1.5'),
    ('npt_1_8', '1/8" NPT'),
    ('npt_1_4', '1/4" NPT'),
    ('quick_disconnect', '快插接头'),
    ('none', '无'),
]

GATING_SYSTEM_RUNNER_TYPE = [
    ('cold_runner', '全冷流道'),
    ('hot_to_cold', '热转冷'),
    ('hot_runner', '全热流道'),
]

HOT_RUNNER_SEQUENCING_CONTROL_METHOD = [
    ('plc_internal', '注塑机PLC控制'),
    ('hot_runner_plc', '热流道系统PLC控制'),
    ('pneumatic_timer', '气动时序器'),
]

HOT_RUNNER_VALVE_DRIVE_TYPE = [
    ('pneumatic', '气动'), 
    ('hydraulic', '液压'), 
    ('electric', '电动')
]

GATE_SHAPE = [
    ('rectangular', '矩形截面'),
    ('circular', '圆形截面'),
    ('annular', '环形'),
    ('diaphragm', '膜片'),
]

LOCATOR_TYPE_CHOICES = [
    ('taper_lock', '锥形锁'),
    ('side_lock', '边锁'),
    ('heel_block', '楔形锁'),
]

GATE_TYPE = [
    ('edge', '侧浇口'),         # rect
    ('pin', '针点浇口'),        # circ
    ('fan', '扇形浇口'),        # rect
    ('tab', '搭接浇口'),        # rect
    ('direct', '直接浇口'),     # circ/rect
    ('sub', '潜伏式浇口'),      # circ
    ('hot_tip', '热流道喷嘴'),  # circ
    ('valve', '阀浇口'),        # circ
]

MOLD_EJECTION_TYPE_CHOICES = [
    ('pin', '顶针式'),
    ('sleeve', '司筒式'),
    ('stripper', '推板式'),
    ('blade', '扁顶针'),
    ('air', '气顶'),
    ('unscrewing', '旋转脱螺纹'),
    ('lifter', '斜顶'),
]

EJECTOR_ROD_HOLE_TYPE = [
    ('center_single', '中心单孔'),
    ('four_point', '四点分布'),
    ('custom', '自定义'),
]

MOLD_HANDLING_TYPE = [
    ('stud_hole', '吊装螺孔'),
    ('lifting_stud', '吊环螺钉'),
    ('lifting_slot', '吊装槽'),
    ('custom', '自定义'),
]

INJECTION_MACHINE_TYPE = [
    ('horizontal', '卧式'),
    ('vertical', '立式'),
]

INJECTION_MACHINE_DRIVE = [
    ('hydraulic', '液压'),
    ('electric', '电动'),
    ('hybrid', '伺服混合'),
]


EJECTION_TYPE_CHOICES = [
    ('hydraulic', '液压顶出'),
    ('mechanical', '机械顶出'),
    ('none', '无顶出（手动取件）'),
]

EJECTION_PATTERN_CHOICES = [
    ('single_center', '单中心顶出'),
    ('four_corner_symmetric', '四角对称顶出'),
    ('none', '无自动顶出'),
]