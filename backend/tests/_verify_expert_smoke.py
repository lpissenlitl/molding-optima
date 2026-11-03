"""expert 侧 smoke 批量 runner：批跑 `process/algorithms/expert/tests/verify_*_smoke.py`。

用法（必须在 backend 目录下运行）：
    ..\\.venv\\Scripts\\python.exe tests\\_verify_expert_smoke.py

判定口径 = **子进程退出码**（非 0 = 该场景不过）—— 与各 smoke 脚本自身的
「`_failures` 收集器 + 退出码」口径一致。

⚠️ 为什么不直接用 pytest：
    `verify_` 前缀 ⇒ pytest **不收集**这些脚本。若把它们改名为 `test_*`，
    pytest 会把「断言值不对」也报成 PASS（假绿）⇒ **不要改前缀**。
    本 runner 存在的意义就是给这批脚本一个统一的批量入口。

⚠️ 与「逐位回归锁」的区别：
    各 smoke 脚本是**断言式**护栏（校验领域不变量）；
    `_snapshot_expert.py` + `_golden_expert.json` 是**逐位**护栏（输出逐条比对）。
    二者互补 —— 逐位锁已于 2026-11-03 退役（生成器不可重建，见
    `backend/_refs/README.md` §维护说明），当前 expert 侧以本 runner 为准。
"""
import glob
import os
import subprocess
import sys

# 本脚本位于 backend/tests/ ⇒ 向上两级 = backend 根目录
BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BACKEND)
sys.path.insert(0, BACKEND)

# ⚠️ 子进程必须显式指定 UTF-8 输出编码：
#    各 smoke 脚本结尾会打印 ✅ / ✓ 等非 ASCII 字符，而 Windows 控制台默认
#    GBK codepage ⇒ 直接跑会抛 UnicodeEncodeError（断言全过却在最后一行崩、
#    退出码 = 1 ⇒ 假失败）。这里对子进程注入 PYTHONIOENCODING 规避。
CHILD_ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")

TESTS_DIR = os.path.join(
    BACKEND, "process", "algorithms", "expert", "tests")
PATTERN = os.path.join(TESTS_DIR, "verify_*_smoke.py")

PASS = "\033[92m"
FAIL = "\033[91m"
NC = "\033[0m"


def main():
    scripts = sorted(glob.glob(PATTERN))
    if not scripts:
        print("未找到 smoke 脚本: %s" % PATTERN)
        return 2

    print("expert smoke 批量运行：%d 个脚本" % len(scripts))
    print("-" * 72)

    failed = []
    for path in scripts:
        name = os.path.basename(path)
        proc = subprocess.run(
            [sys.executable, path],
            cwd=BACKEND,
            env=CHILD_ENV,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        ok = proc.returncode == 0
        print("%s %-38s exit=%d%s" % (
            (PASS + "PASS" + NC) if ok else (FAIL + "FAIL" + NC),
            name,
            proc.returncode,
            ""))
        if not ok:
            failed.append((name, proc))

    print("-" * 72)
    if not failed:
        print("%s全部通过：%d/%d%s" % (PASS, len(scripts), len(scripts), NC))
        return 0

    print("%s失败：%d/%d%s" % (FAIL, len(failed), len(scripts), NC))
    for name, proc in failed:
        print("\n===== %s (exit=%d) =====" % (name, proc.returncode))
        tail = (proc.stdout or "")[-2000:]
        err = (proc.stderr or "")[-2000:]
        if tail.strip():
            print("--- stdout(tail) ---")
            print(tail)
        if err.strip():
            print("--- stderr(tail) ---")
            print(err)
    return 1


if __name__ == "__main__":
    sys.exit(main())
