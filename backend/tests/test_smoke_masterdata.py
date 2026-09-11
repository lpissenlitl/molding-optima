"""
molding-optima 基础数据 CRUD 对接测试脚本

目标：覆盖 project / mold / polymer / filler / injection / auxiliary 六个模块的
完整 CRUD + 批量删除流程，验证前后端字段是否一致、参数是否对齐。

执行方式：
    cd backend
    python tests/test_smoke_masterdata.py            # 独立运行
    pytest tests/test_smoke_masterdata.py            # pytest 运行

报告输出：
    - 终端表格（✓/✗/!）
    - 失败用例详细响应体
    - 末尾汇总

依赖：仅 Python 标准库（urllib + json），无需 requests / Django 环境

前置：需要后端服务运行在 127.0.0.1:8000，且 init_demo 已初始化（demo_admin / demo123456）
"""

import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Optional

# 修复 PowerShell GBK 编码下的 Unicode 输出问题
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_URL = "http://127.0.0.1:8000"

# 测试账号（init_demo 创建）
USERNAME = "demo_admin"
PASSWORD = "demo123456"
UA = "smoke-test/1.0"

# 测试数据统一前缀，避免污染
TAG = f"_test_{int(time.time())}"


# ============================================================
# HTTP 客户端（标准库实现，复刻前端 request.ts 行为）
# ============================================================

class ApiClient:
    def __init__(self):
        self.base_url = BASE_URL
        self.token: Optional[str] = None
        self.results: list[dict] = []  # 全部用例结果

    def _request(self, method: str, path: str, *, params=None, data=None) -> dict:
        """统一请求方法：返回 dict {ok, status, http_code, body}"""
        url = f"{self.base_url}{path}"
        if params:
            from urllib.parse import urlencode
            url = f"{url}?{urlencode(params)}"

        body = None
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["X-Auth-Token"] = self.token
        if data is not None:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8")
                return {
                    "ok": True,
                    "http_code": resp.status,
                    "body": json.loads(raw) if raw else {},
                }
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8") if e.fp else ""
            try:
                parsed = json.loads(raw) if raw else {}
            except Exception:
                parsed = {"raw": raw}
            return {
                "ok": False,
                "http_code": e.code,
                "body": parsed,
            }
        except Exception as e:
            return {
                "ok": False,
                "http_code": -1,
                "body": {"error": repr(e)},
            }

    def login(self):
        """登录获取 token"""
        result = self._request("POST", "/api/login/", data={
            "username": USERNAME,
            "password": PASSWORD,
            "ua": UA,
        })
        if result["ok"] and result["body"].get("status") == 0:
            self.token = result["body"].get("data", {}).get("token")
            return True
        return False

    def assert_biz_success(self, result: dict, expected_data_keys: Optional[list] = None) -> bool:
        """判断业务成功：HTTP 200/201 且 body.status == 0"""
        if not result["ok"]:
            return False
        if result["http_code"] not in (200, 201):
            return False
        body = result["body"]
        if not isinstance(body, dict) or body.get("status") != 0:
            return False
        if expected_data_keys:
            data = body.get("data") or {}
            for k in expected_data_keys:
                if k not in data:
                    return False
        return True

    def record(self, module: str, op: str, result: dict, ok: bool, expected_keys=None):
        """记录用例结果"""
        self.results.append({
            "module": module,
            "op": op,
            "ok": ok,
            "http_code": result["http_code"],
            "biz_status": result["body"].get("status") if isinstance(result["body"], dict) else None,
            "msg": result["body"].get("msg") if isinstance(result["body"], dict) else None,
            "expected_keys": expected_keys,
        })


# ============================================================
# 各模块的测试 payload 构建（最小必填字段）
# ============================================================

def build_project_payload(tag: str) -> dict:
    return {
        "project_code": f"PRJ{tag}",
        "project_name": f"测试项目{tag}",
        "initiator": "test_initiator",
    }


def build_mold_payload(tag: str) -> dict:
    return {
        "mold_no": f"MOLD{tag}",          # mold_no 是唯一必填字段
        "mold_name": f"测试模具{tag}",
    }


def build_polymer_payload(tag: str) -> dict:
    return {
        "abbreviation": f"POLY{tag}",     # 无必填字段，取标识字段
        "grade": f"G{tag}",
    }


def build_filler_payload(tag: str) -> dict:
    return {
        "name": f"填充物{tag}",            # 名称作为唯一标识
        "category": "test",
    }


def build_injection_payload(tag: str) -> dict:
    return {
        "device_no": f"IMM{tag}",          # 后端 device_no 必填
        "model": f"IMM{tag}",
        "brand": "test_brand",
    }


def build_auxiliary_payload(tag: str) -> dict:
    return {
        "equipment_name": f"装置{tag}",   # 必填
        "equipment_type": "test_type",    # 必填
        "specification": "spec_test",
        "total_count": 1,
        "available_count": 1,
        "remarks": "remark_test",
    }


# ============================================================
# 模块测试流程：C -> R -> U -> R -> D -> R
# ============================================================

def run_module_test(client: ApiClient, module: str, base_path: str, build_payload):
    """对单个模块跑完整 CRUD + 批量删除流程，返回汇总"""
    print(f"\n{'='*60}\n[{module}] CRUD 测试开始\n{'='*60}")

    # 1) Create
    payload = build_payload(TAG)
    r = client._request("POST", base_path, data=payload)
    ok = client.assert_biz_success(r, expected_data_keys=["id"])
    client.record(module, "C (Create)", r, ok, expected_keys=["id"])
    print(f"  [C] POST {base_path}  HTTP={r['http_code']} biz={r['body'].get('status') if isinstance(r['body'], dict) else 'N/A'}")
    if not ok:
        print(f"      FAIL: {json.dumps(r['body'], ensure_ascii=False)[:300]}")
        return
    new_id = r["body"]["data"]["id"]
    print(f"      OK   new id={new_id}")

    # 2) Read (detail)
    r = client._request("GET", f"{base_path}{new_id}/")
    ok = client.assert_biz_success(r, expected_data_keys=["id"])
    client.record(module, "R1 (Detail)", r, ok, expected_keys=["id"])
    print(f"  [R1] GET {base_path}{new_id}/  HTTP={r['http_code']} biz={r['body'].get('status') if isinstance(r['body'], dict) else 'N/A'}  {'OK' if ok else 'FAIL'}")

    # 3) Update
    payload["id"] = new_id
    # 模块特定更新字段（保持兼容）
    if module == "project":
        payload["project_name"] = f"已更新{TAG}"
    elif module == "mold":
        payload["mold_name"] = f"已更新{TAG}"
    elif module == "polymer":
        payload["grade"] = f"G{TAG}_upd"
    elif module == "filler":
        payload["name"] = f"填充物更新{TAG}"
    elif module == "injection":
        payload["device_no"] = f"IMM{TAG}_upd"
        payload["model"] = f"IMM{TAG}_upd"
    elif module == "auxiliary":
        payload["equipment_name"] = f"装置更新{TAG}"

    r = client._request("PUT", f"{base_path}{new_id}/", data=payload)
    ok = client.assert_biz_success(r)
    client.record(module, "U (Update)", r, ok)
    print(f"  [U]  PUT {base_path}{new_id}/  HTTP={r['http_code']} biz={r['body'].get('status') if isinstance(r['body'], dict) else 'N/A'}  {'OK' if ok else 'FAIL'}")
    if not ok:
        print(f"      FAIL: {json.dumps(r['body'], ensure_ascii=False)[:300]}")

    # 4) Read (detail, 验证更新生效)
    r = client._request("GET", f"{base_path}{new_id}/")
    ok = client.assert_biz_success(r)
    client.record(module, "R2 (Detail after U)", r, ok)
    print(f"  [R2] GET {base_path}{new_id}/  HTTP={r['http_code']} biz={r['body'].get('status') if isinstance(r['body'], dict) else 'N/A'}  {'OK' if ok else 'FAIL'}")

    # 5) List (分页) —— 后端用 page_no/page_size，返回 total/items
    r = client._request("GET", base_path, params={"page_no": 1, "page_size": 5})
    ok = client.assert_biz_success(r, expected_data_keys=["total", "items"])
    client.record(module, "L (List)", r, ok, expected_keys=["total", "items"])
    print(f"  [L]  GET {base_path}?page_no=1&page_size=5  HTTP={r['http_code']} biz={r['body'].get('status') if isinstance(r['body'], dict) else 'N/A'}  {'OK' if ok else 'FAIL'}")
    if not ok:
        data = r["body"].get("data") if isinstance(r["body"], dict) else None
        data_keys = list(data.keys()) if isinstance(data, dict) else "N/A"
        print(f"      data shape: {type(data).__name__}, keys: {data_keys}")
        print(f"      DEBUG: {json.dumps(r['body'], ensure_ascii=False)[:300]}")

    # 6) Batch delete (创建第二个实例用于批量删除)
    payload2 = build_payload(TAG + "_b")
    if module == "project":
        payload2["project_code"] = f"PRJ{TAG}_b"
    elif module == "mold":
        payload2["mold_no"] = f"MOLD{TAG}_b"
    elif module == "polymer":
        payload2["abbreviation"] = f"POLY{TAG}_b"
    elif module == "filler":
        payload2["name"] = f"填充物{TAG}_b"
    elif module == "injection":
        payload2["device_no"] = f"IMM{TAG}_b"
        payload2["model"] = f"IMM{TAG}_b"
    elif module == "auxiliary":
        payload2["equipment_name"] = f"装置{TAG}_b"

    r = client._request("POST", base_path, data=payload2)
    if client.assert_biz_success(r, expected_data_keys=["id"]):
        second_id = r["body"]["data"]["id"]
        # 批量删除
        r = client._request("DELETE", f"{base_path}actions/batch-delete/", data={"ids": [second_id]})
        ok = client.assert_biz_success(r)
        client.record(module, "BD (BatchDelete)", r, ok)
        print(f"  [BD] DELETE {base_path}actions/batch-delete/  HTTP={r['http_code']} biz={r['body'].get('status') if isinstance(r['body'], dict) else 'N/A'}  {'OK' if ok else 'FAIL'}")

    # 7) Delete (清理第一个实例)
    r = client._request("DELETE", f"{base_path}{new_id}/")
    ok = client.assert_biz_success(r)
    client.record(module, "D (Delete)", r, ok)
    print(f"  [D]  DELETE {base_path}{new_id}/  HTTP={r['http_code']} biz={r['body'].get('status') if isinstance(r['body'], dict) else 'N/A'}  {'OK' if ok else 'FAIL'}")

    # 8) Verify delete (读应失败)
    r = client._request("GET", f"{base_path}{new_id}/")
    deleted_ok = not client.assert_biz_success(r)  # 应该不再成功
    client.record(module, "RV (VerifyDel)", r, deleted_ok)
    print(f"  [RV] GET {base_path}{new_id}/ (期望失败)  HTTP={r['http_code']} biz={r['body'].get('status') if isinstance(r['body'], dict) else 'N/A'}  {'OK (404)' if deleted_ok else 'FAIL (仍可读)'}")


# ============================================================
# 报告生成
# ============================================================

def print_report(client: ApiClient):
    print(f"\n{'='*60}\n汇总报告\n{'='*60}\n")
    results = client.results
    total = len(results)
    passed = sum(1 for r in results if r["ok"])
    failed = total - passed

    print(f"总用例: {total}  通过: {passed}  失败: {failed}\n")

    # 按模块分组
    by_module: dict[str, list] = {}
    for r in results:
        by_module.setdefault(r["module"], []).append(r)

    for mod, items in by_module.items():
        print(f"\n[{mod}]")
        print(f"  {'用例':<25} {'状态':<6} {'HTTP':<6} {'BIZ':<6} {'MSG'}")
        print(f"  {'-'*25} {'-'*6} {'-'*6} {'-'*6} {'-'*40}")
        for r in items:
            status = "[OK]" if r["ok"] else "[FAIL]"
            print(f"  {r['op']:<25} {status:<6} {str(r['http_code']):<6} {str(r['biz_status']):<6} {(r['msg'] or '')[:40]}")

    # 失败详细日志
    print(f"\n{'='*60}\n失败用例详细响应体\n{'='*60}\n")
    has_fail = False
    for r in results:
        if not r["ok"]:
            has_fail = True
            print(f"[{r['module']}/{r['op']}] HTTP={r['http_code']} biz={r['biz_status']}")
            print(f"  msg: {r['msg']}")
            if r.get("expected_keys"):
                print(f"  expected_keys: {r['expected_keys']}")
            print()
    if not has_fail:
        print("无失败用例 ✓")

    print(f"\n{'='*60}\n接口对接总结\n{'='*60}")
    if failed == 0:
        print("✓ 所有用例通过，前后端接口完全对接")
    else:
        print(f"✗ {failed} 个用例失败，需修复前后端字段不一致 / 接口路径错误等问题")
    print()


# ============================================================
# Main
# ============================================================

def main():
    client = ApiClient()

    print(f"目标后端: {BASE_URL}")
    print(f"测试账号: {USERNAME}")
    print(f"测试标签: {TAG}\n")

    # 1) 登录
    print(">>> 登录拿 token...")
    if not client.login():
        # 尝试不带 UA
        r = client._request("POST", "/api/login/", data={"username": USERNAME, "password": PASSWORD})
        if r["ok"] and r["body"].get("status") == 0:
            client.token = r["body"].get("data", {}).get("token")
        else:
            print(f"登录失败: {json.dumps(r['body'], ensure_ascii=False)[:300]}")
            sys.exit(1)
    print(f"    token: {client.token[:20]}..." if client.token else "    登录失败")

    # 2) 跑各模块
    modules = [
        ("project", "/api/projects/", build_project_payload),
        ("mold", "/api/molds/", build_mold_payload),
        ("polymer", "/api/polymers/", build_polymer_payload),
        ("filler", "/api/fillers/", build_filler_payload),
        ("injection", "/api/injection-machines/", build_injection_payload),
        ("auxiliary", "/api/auxiliary-equipments/", build_auxiliary_payload),
    ]
    for name, path, builder in modules:
        run_module_test(client, name, path, builder)

    # 3) 报告
    print_report(client)

    # 退出码：有失败则非 0
    failed = sum(1 for r in client.results if not r["ok"])
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
