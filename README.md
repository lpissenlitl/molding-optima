# molding-optima · 智能工艺系统

> 面向**注射成型工艺**领域的智能工艺优化系统。

**核心使命**：

> 1. **辅助工艺人员设置工艺参数**（从零开始 → 基于规则推荐）
> 2. **缺陷出现后自动调整工艺参数**（人工排查 → 标记缺陷即得建议）

---

## 🏗 架构概览

```
molding-optima/
├── backend/                # Django 5.2 + DRF 后端
│   ├── _moldx/             # Django 脚手架（settings/urls/wsgi）
│   ├── extensions/         # 公共扩展（异常/schema/视图基类）
│   ├── utils/              # 通用工具
│   ├── identity/           # 用户管理（用户/组织/角色）
│   ├── masterdata/         # 基础数据（模具/材料/设备）
│   ├── process/            # 工艺管理（工艺参数/优化引擎/调模/规则）
│   ├── filecenter/         # 文件中心
│   ├── reporting/          # 报表
│   └── bootstrap/          # 初始化脚本
│
├── frontend/               # Vue 3 + Vite 5 + TS 前端
│   ├── src/
│   │   ├── api/            # API 封装
│   │   ├── styles/         # 全局样式（五层架构）
│   │   ├── views/          # 业务页面
│   │   └── ...
│   └── README.md           # 前端详细文档
│
├── docs/                   # 设计文档
├── old/                    # 历史代码（重构前）
├── prototype/              # 页面原型
├── architecture.md         # 架构文档（含 ADR）
└── 重构方案.md              # 重构方案
```

> 详见 [architecture.md](./architecture.md)（架构决策与模块划分）

---

## 🚀 快速开始

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 使用 pip-tools 双文件依赖管理：
#   requirements.in  = 顶层依赖（手工维护）
#   requirements.txt = lock file（pip-compile 生成）
pip install pip-tools
pip-sync requirements.txt   # 同步 venv 到 lock 文件一致

# 数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动开发服务器（默认端口 8200）
python manage.py runserver 0.0.0.0:8200
```

> **依赖管理**（pip-tools）：
> - 加新包：编辑 `requirements.in` → `pip-compile requirements.in` → `pip-sync`
> - 升级包：`pip-compile --upgrade-package <name>` in requirements.in` → `pip-sync`
> - 生产部署（Linux）：`pip install -r requirements.txt` + `pip install 'uwsgi>=2.0.21'`（uwsgi 不进 lock file，部署层单独处理）
>
> **镜像源配置**（如需国内镜像加速）：
> - pip 全局配置位置：`C:\Users\<user>\pip\pip.ini`（Windows）或 `~/.config/pip/pip.conf`（Linux）
> - 配置示例：`global.index-url = https://mirrors.aliyun.com/pypi/simple/`
> - pip-compile 默认会把 `index-url` 写入生成的 lock file。加 `--no-emit-index-url` 开关让 `requirements.txt` 保持纯依赖列表（推荐）。

### 前端

```bash
cd frontend
npm install
npm run dev  # 默认端口 9527，自动代理 /api → 8200
```

启动后访问 http://localhost:9527/

---

## 🛠 技术栈

### 后端
- **Python** 3.11
- **Django** 5.2
- **Django REST Framework**
- **MySQL**（单库，与 molding-expert 主线对齐）
- **Pydantic**（Schema 校验）

### 前端
- **Vue 3** + **Vite 5** + **TypeScript**
- **Pinia**（状态）+ **Vue Router 4**（路由）
- **Element Plus**（UI 库，CSS 变量驱动主题）
- **SCSS**（设计令牌 + Mixin，详见 [frontend/README.md](./frontend/README.md)）

---

## 📦 业务模块

| 模块 | 后端 app | 前端目录 | 职责 |
|---|---|---|---|
| **用户管理** | `identity/` | `views/identity/` | 用户/组织/角色权限 |
| **基础数据** | `masterdata/` | `views/masterdata/` | 模具/材料/设备 |
| **工艺管理** | `process/` | `views/process/` | 工艺参数/优化引擎/调模/规则 |
| **文件中心** | `filecenter/` | （融入各模块）| 文件上传/下载 |
| **报表** | `reporting/` | （融入工艺模块）| 工艺参数导出 |
| **初始化** | `bootstrap/` | - | 数据库初始化/字典/默认账号 |

---

## 🎯 项目边界（明确不做什么）

- ❌ **不替代工艺师最终决策**（系统建议，决策权在人）
- ❌ **不做实时闭环控制**（不直连注塑机）
- ❌ **不做生产排程/设备监控/模流仿真/试模管理**（与 molding-expert 业务边界对齐）

---

## 🔗 与上游系统关系

`molding-optima` 是 `molding-expert` 的独立子模块：

- **数据契约一致**：通过同一份后端 API 契约对齐
- **技术栈独立**：molding-optima（Vue 3 + Django 5.2）与 molding-expert（Vue 2 + Django 5.2）各自演进
- **不强制融合**：独立共存是长期状态

详见 [architecture.md §6 与上游系统的关系](./architecture.md#六架构演进路线)

---

## 📚 文档索引

| 文档 | 用途 |
|---|---|
| [architecture.md](./architecture.md) | **架构文档**（模块划分 + ADR 决策记录）|
| [重构方案.md](./重构方案.md) | 重构方案与边界 |
| [frontend/README.md](./frontend/README.md) | 前端详细文档 |
| [docs/](./docs/) | 业务设计文档（如工艺调整设计）|

---

## 📝 版本

**当前版本**：v0.5
**最后更新**：2026-09-02