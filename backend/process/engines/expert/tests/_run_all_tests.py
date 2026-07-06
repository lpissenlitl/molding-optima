"""运行所有 smoke test"""
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

tests = [
    'test_inj_time_smoke.py',
    'test_vp_switch_mode_smoke.py',
    'test_cool_time_smoke.py',
    'test_hold_time_smoke.py',
    'test_hold_velo_smoke.py',
    'test_meter_back_pres_smoke.py',
    'test_meter_pres_smoke.py',
    'test_meter_speed_smoke.py',
    'test_suckback_smoke.py',
    'test_temperature_smoke.py',
]

total_pass = 0
total_fail = 0
results = []

for test in tests:
    print(f'\n--- Running {test} ---')
    result = subprocess.run(
        [sys.executable, test],
        capture_output=True,
        text=True,
    )
    
    # 解析输出
    output = result.stdout + result.stderr
    for line in output.split('\n'):
        if 'Total:' in line:
            print(f'  {line.strip()}')
        if 'PASS:' in line:
            # 提取数字
            parts = line.split('PASS:')
            if len(parts) > 1:
                try:
                    n = int(parts[1].split()[0])
                    total_pass += n
                except:
                    pass
        if 'FAIL:' in line:
            parts = line.split('FAIL:')
            if len(parts) > 1:
                try:
                    n = int(parts[1].split()[0])
                    total_fail += n
                    results.append(f'{test}: {n} failures')
                except:
                    pass

print('\n' + '=' * 60)
print(f'SUMMARY: {total_pass} passed, {total_fail} failed')
if results:
    print('\nFailed tests:')
    for r in results:
        print(f'  - {r}')
else:
    print('\n[OK] All smoke tests passed!')
