"""D+B 修复前 vs 修复后 的真实引擎输出对比（2026-10-23）

只读脚本：读两份 before_after 存档 JSON，不碰 DB、不改代码。

背景：
    - `_before_after.json`       = 修 D+B **之前**跑的（接线已完成，推理层未修）
    - `_before_after_db.json`    = 修 D+B **之后**跑的

两份存档的「当前态」（脚本里的 after_*）用的是同一套代码路径，
差异**只**来自 D（无效激活过滤）+ B（门控取连接列）这两处推理层修复。

输出：
    1) 聚合：条数 / 参数集合 / 推荐值+置信度 的变化
    2) 参数级：哪些参数被剔除、哪些保留
    3) 逐样本明细

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/_diff_db_effect.py
"""

import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding='gbk', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
OLD_FILE = os.path.join(HERE, '_before_after.json')       # D+B 前
NEW_FILE = os.path.join(HERE, '_before_after_db.json')    # D+B 后


def hr(t):
    print()
    print('=' * 96)
    print(t)
    print('=' * 96)


def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def head_map(items):
    """head 列表 → {param: (recommended_value, confidence)}"""
    out = {}
    for r in items or []:
        out[r.get('param')] = (r.get('recommended_value'), r.get('confidence'))
    return out


def main():
    old = load(OLD_FILE)
    new = load(NEW_FILE)

    o_by_id = {d['parameter_id']: d for d in old['details']}
    n_by_id = {d['parameter_id']: d for d in new['details']}
    ids = sorted(set(o_by_id) & set(n_by_id))

    hr('1. 聚合：推荐条数 / 参数集合 的变化（D+B 前 → D+B 后）')
    cnt_changed = set_changed = val_changed = 0
    total_o = total_n = 0
    dropped = {}
    kept = {}
    added = {}

    for pid in ids:
        o = o_by_id[pid]
        n = n_by_id[pid]
        total_o += o['after_count']
        total_n += n['after_count']
        op, np_ = o['after_params'], n['after_params']
        if o['after_count'] != n['after_count']:
            cnt_changed += 1
        if set(op) != set(np_):
            set_changed += 1
        for p in op:
            if p not in np_:
                dropped[p] = dropped.get(p, 0) + 1
        for p in np_:
            if p not in op:
                added[p] = added.get(p, 0) + 1
            else:
                kept[p] = kept.get(p, 0) + 1
        om, nm = head_map(o['after_head']), head_map(n['after_head'])
        for p in set(om) & set(nm):
            if om[p] != nm[p]:
                val_changed += 1
                break

    print(f'  样本数                : {len(ids)}')
    print(f'  推荐总条数            : {total_o} → {total_n}'
          f'（{total_n - total_o:+d}，平均 {total_o / len(ids):.2f} → {total_n / len(ids):.2f}）')
    print(f'  条数变化的样本        : {cnt_changed} / {len(ids)}')
    print(f'  参数集合变化的样本    : {set_changed} / {len(ids)}')
    print(f'  推荐值/置信度变化的样本: {val_changed} / {len(ids)}')

    hr('2. 参数级：保留 / 剔除 / 新增')
    print('  【保留】（前后都在）:')
    for p, c in sorted(kept.items(), key=lambda kv: -kv[1]):
        print(f'    {p:<22} {c} 个样本')
    print('  【剔除】（D+B 前有，D+B 后没了）:')
    for p, c in sorted(dropped.items(), key=lambda kv: -kv[1]):
        print(f'    {p:<22} {c} 个样本')
    print('  【新增】（D+B 后才有）:')
    for p, c in sorted(added.items(), key=lambda kv: -kv[1]):
        print(f'    {p:<22} {c} 个样本')

    hr('3. 逐样本明细（前 8 个）')
    for pid in ids[:8]:
        o = o_by_id[pid]
        n = n_by_id[pid]
        print(f'  parameter_id={pid}  条数 {o["after_count"]} → {n["after_count"]}')
        print(f'    前: {o["after_params"]}')
        print(f'    后: {n["after_params"]}')

    hr('4. 单样本推荐明细对照（parameter_id=%s）' % ids[0])
    o = o_by_id[ids[0]]
    n = n_by_id[ids[0]]
    print('  --- D+B 前 ---')
    for r in o['after_head']:
        print(f'    cur={r.get("current_value")} rec={r.get("recommended_value")} '
              f'conf={r.get("confidence")} param={r.get("param")}')
    print('  --- D+B 后 ---')
    for r in n['after_head']:
        print(f'    cur={r.get("current_value")} rec={r.get("recommended_value")} '
              f'conf={r.get("confidence")} param={r.get("param")}')

    print()
    print('=' * 96)
    print('对比结束（只读，未写库、未改产品代码）')
    print('=' * 96)
    return 0


if __name__ == '__main__':
    sys.exit(main())
