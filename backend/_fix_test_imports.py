"""批量修复测试文件中的内部方法调用"""
import os

tests_dir = r'f:\items\moldingx\molding-optima\backend\process\engines\expert\tests'

# 需要添加的 import
imports_to_add = """
from process.engines.expert.algorithm_engine import AlgorithmEngine  # noqa: E402
from process.engines.expert.helpers import parse_material_family  # noqa: E402"""

test_files = [
    'test_meter_speed_smoke.py',
    'test_meter_pres_smoke.py',
    'test_meter_back_pres_smoke.py',
    'test_hold_time_smoke.py',
]

for test_file in test_files:
    filepath = os.path.join(tests_dir, test_file)
    if not os.path.exists(filepath):
        print(f'Skipping {test_file} (not found)')
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 添加 import
    if 'from process.engines.expert.algorithm_engine import AlgorithmEngine' not in content:
        lines = content.split('\n')
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith('from process.engines.expert'):
                lines.insert(i + 1, imports_to_add.strip())
                break
        content = '\n'.join(lines)
    
    # 简单字符串替换
    # 只替换 init._xxx 为 init.engine._xxx（不包括已经含 .engine. 的）
    # 需要匹配 init._coeffs, init._get_xxx, init._compute_xxx 等
    
    # 替换 init._coeffs (但不是 init.engine._coeffs)
    content = content.replace('init._coeffs', 'init.engine._coeffs')
    
    # 替换 init._get_xxx
    content = content.replace('init._get_', 'init.engine._get_')
    content = content.replace('init._compute_', 'init.engine._compute_')
    content = content.replace('init._apply_', 'init.engine._apply_')
    content = content.replace('init._derive_', 'init.engine._derive_')
    
    # 替换 init._parse_family (替换为全局函数)
    content = content.replace('init._parse_family', 'parse_material_family')
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {test_file}')
    else:
        print(f'No changes needed for {test_file}')

print('Done!')
