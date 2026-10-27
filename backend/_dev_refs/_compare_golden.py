"""黄金快照比对：新快照 vs 基线快照（逐条 diff，2026-10-23）

用法：
    ..\.venv\Scripts\python.exe _dev_refs\_compare_golden.py _dev_refs\_golden_E4b.json _dev_refs\_golden_E4c_check.json

口径（比 E4-b 记录的口径更强）：**整棵 JSON 逐条相等**才算通过；
若只比 summary 会漏掉文案/顺序/浮点尾数的变化。
"""
import json
import sys


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def walk(a, b, path="", out=None):
    """递归比对，产出差异描述列表。"""
    out = out if out is not None else []
    if type(a) is not type(b):
        out.append((path, repr(a)[:120], repr(b)[:120]))
        return out
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append((f"{path}.{k}", "<缺失>", repr(b[k])[:120]))
            elif k not in b:
                out.append((f"{path}.{k}", repr(a[k])[:120], "<缺失>"))
            else:
                walk(a[k], b[k], f"{path}.{k}", out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append((f"{path}[len]", len(a), len(b)))
            return out
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", out)
    else:
        if a != b:
            out.append((path, repr(a)[:120], repr(b)[:120]))
    return out


def main():
    base_path, new_path = sys.argv[1], sys.argv[2]
    base, new = load(base_path), load(new_path)

    diffs = walk(base, new)
    print(f"基线：{base_path}")
    print(f"新快照：{new_path}")
    print(f"逐条差异数：{len(diffs)}")
    if diffs:
        for path, a, b in diffs[:40]:
            print(f"  {path}\n      基线={a}\n      新  ={b}")
        if len(diffs) > 40:
            print(f"  ...（其余 {len(diffs) - 40} 条略）")
    else:
        print("PASS —— 两份快照逐条完全相等")


if __name__ == "__main__":
    main()
