# 砺剑AWDp — Attack With Defense Plus 比赛平台

> 砺剑铸盾，攻防制胜

AWDP 结合 **Break（攻击）** 与 **Fix（修复）** 两个环节的 CTF 比赛平台，基于 Flask + Docker 构建，支持动态积分、容器管理、自动防御评估。

---

## 目录

- [架构概览](#架构概览)
- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [出题模板](#出题模板)
- [防御评估系统](#防御评估系统)
- [项目结构](#项目结构)
- [API 路由](#api-路由)
- [备份与迁移](#备份与迁移)
- [配置说明](#配置说明)
- [小行星大屏可视化](#小行星大屏可视化)

---

## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    砺剑AWDp Platform                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ 认证系统   │  │  题目管理  │  │  容器管理 (Docker)   │  │
│  │ (auth.py) │  │ (main.py)│  │  (docker_manager)   │  │
│  └──────────┘  └──────────┘  └──────────────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ 计分引擎   │  │ 后台调度  │  │  防御评估系统         │  │
│  │(scoring)  │  │(scheduler)│  │  (evaluate_defense) │  │
│  └──────────┘  └──────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                     SQLite / PostgreSQL                   │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐    ┌──────────────────┐
│  awdp-sqli       │    │  awdp-ssrf       │
│  (挑战容器)       │    │  (挑战容器)       │
│  127.0.0.1:3xxxx │    │  127.0.0.1:3xxxx │
└──────────────────┘    └──────────────────┘
```

- **平台** — Python Flask Web 应用，管理用户、比赛、计分
- **容器** — 每个队伍每道题一个独立 Docker 容器，注入动态 Flag
- **评估** — 防御补丁提交后自动在临时容器中运行 EXP 验证
- **调度** — 后台服务定时健康检查、Flag 刷新、轮次切换

---

## 功能特性

### 核心玩法
| 环节 | 说明 |
|------|------|
| **Break（攻击）** | 启动靶机容器，挖掘漏洞获取 Flag 提交，动态积分 |
| **Fix（修复）** | 上传补丁包修复漏洞，系统自动检测，成功获得防御分 |
| **动态 Flag** | 每容器独立生成，定时自动刷新，历史 Flag 过期失效 |
| **血榜** | First / Second / Third Blood 标记，额外排名加成 |

### 计分规则
- **Break 得分** — `max(初始分 - (解题数-1) × 递减, 最低分)`
- **排名加成** — 前 20 名解出者获得 5%~3.1% 额外加成
- **Fix 得分** — 每次修复成功获得固定防御分
- **总分** — 攻击分 + 防御分

### 管理功能
- 比赛管理（创建、起止时间、轮次控制）
- 题目管理（Docker 镜像、端口映射、动态 Flag 开关、启用开关）
- 容器监控（状态查看、Flag 手动刷新）
- 防护包评估队列
- 数据导出（CSV）
- 队伍管理（管理员设置、密码重置）
- 排行榜冻结

---

## 快速开始

### 环境要求

- Python 3.9+
- Docker（容器管理和防御评估需要）
- 操作系统：Windows / Linux

### 方式一：本地运行

```bash
# 1. 克隆项目
git clone <repo-url> && cd awdp-platform

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate   # Linux
# venv\Scripts\activate    # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库 (创建管理员 admin / admin)
python run.py init-db

# 5. 启动服务
python run.py run
```

访问 http://127.0.0.1:5000

### 方式二：Docker 部署

```bash
# 1. 构建平台容器
cd deploy
docker compose up -d --build

# 2. 加载挑战镜像（如果有）
docker load -i ../backup/<backup>/images/awdp-sqli.tar
docker load -i ../backup/<backup>/images/awdp-ssrf.tar
```

### 方式三：Docker 迁移（从 Windows 到 Linux）

参见下方 [备份与迁移](#备份与迁移) 章节。

---

## 使用指南

### 管理员入门

| 步骤 | 操作 |
|------|------|
| 1 | 登录 `admin / admin`，访问 `/admin` |
| 2 | **创建比赛** — 设置名称、起止时间 |
| 3 | **添加题目** — 填写信息、绑定 Docker 镜像、设置积分和防御参数（EXP 命令等） |
| 4 | **管理轮次** — 为比赛添加时间轮次 |
| 5 | 选手注册后即可开始比赛 |

### 选手入门

| 步骤 | 操作 |
|------|------|
| 1 | 注册队伍 → 登录 |
| 2 | 首页选择比赛 → 进入比赛详情 |
| 3 | 点击题目 → **启动容器**（获取靶机地址和 Flag） |
| 4 | **Break** — 挖掘漏洞提交 Flag |
| 5 | **Fix** — 编写补丁包 `.tar.gz` → 上传 → 等待评估 |

### 防护包 Fix 要求

- 必须是 `.tar.gz` 格式
- 必须包含 `update.sh`（入口脚本）
- `update.sh` 中必须引用 `/var/www/html`（Web 根目录）
- `update.sh` 负责替换/修补有漏洞的文件，然后重启 Web 服务
- 评估系统将补丁包应用到目标容器，重新运行 EXP 验证

示例 `update.sh`:

```bash
#!/bin/sh
# 覆盖有漏洞的文件
cp /tmp/defpatch/index.php /var/www/html/index.php
# 重启 Apache
apachectl restart
```

---

## 出题模板

项目提供了标准出题模板，位于 `challenges/_template/`：

```
challenges/_template/
├── Dockerfile          # php:8.1-apache 基础镜像
├── build.sh            # 构建脚本: ./build.sh awdp-<题目名>
├── exp.py              # 防御评估 EXP 脚本 (Python, --target 参数)
└── web/
    ├── index.php       # 漏洞入口文件
    └── start.sh        # 容器启动脚本 (写 FLAG, 启服务)
```

### 出题步骤

```bash
# 1. 复制模板
cp -r challenges/_template challenges/my-challenge

# 2. 修改 web/index.php — 编写漏洞代码
#    动态 Flag 读取方式: $flag = trim(file_get_contents('/flag'));

# 3. 修改 Dockerfile — 添加额外依赖

# 4. 编写 exp.py（影响防御评估结果）
#    exit(0) = 攻击成功 / 修复失败
#    exit(1) = 攻击被拦截 / 修复成功
#    脚本必须支持 --target 参数

# 5. 构建镜像
cd challenges/my-challenge
./build.sh awdp-my-challenge

# 6. 管理员后台 → 添加题目
#    Docker 镜像填: awdp-my-challenge
#    容器内部端口: 80 (外部端口留空自动分配)
#    EXP 命令填: python3 /opt/exp.py --target http://127.0.0.1:{PORT}
```

### 关键约定

| 约定 | 说明 |
|------|------|
| `$FLAG` 环境变量 | 平台创建容器时注入，`start.sh` 负责写入文件 |
| `/flag` 文件 | 标准 Flag 读取路径，PHP 代码通过 `file_get_contents('/flag')` 读取 |
| `exp_cmd` 配置 | 管理员在题目中配置 EXP 命令，平台注入 `exp.py` 到 `/opt/exp.py` 并执行 |
| 镜像命名 | `awdp-<题目名>` 前缀，平台据此定位 `challenges/<目录>/exp.py` |

### EXP 脚本规范

`exp.py` 在防御评估时被 **注入到测试容器的 `/opt/exp.py`** 并执行，通过退出码判断修复效果：

```python
#!/usr/bin/env python3
"""测试漏洞是否可被利用"""
import argparse
import urllib.request
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--target', default='http://127.0.0.1')
args = parser.parse_args()

base = args.target.rstrip('/')
body = urllib.request.urlopen(f'{base}/?id=1%20AND%201=2', timeout=10).read().decode()

if 'error' in body:
    # 漏洞仍可利用 → 修复失败
    sys.exit(0)
else:
    # 漏洞已被修补 → 修复成功
    sys.exit(1)
```

---

## 防御评估系统

`evaluate_defense.py` 是独立的评估脚本，流程：

```
上传补丁包 → 排队 → 启动临时容器 → 应用补丁 → 运行 EXP → 判分
```

1. **解包** — 验证 `.tar.gz` 结构
2. **启动** — 基于 `challenge.docker_image` 启动临时 Docker 容器
3. **应用** — 复制补丁文件到容器，执行 `update.sh`
4. **重启** — 重启 Apache 使补丁生效
5. **注入 exp.py** — 将 `challenges/<目录>/exp.py` 注入到容器 `/opt/exp.py`
6. **攻击** — 运行 `challenge.exp_cmd`（支持 `{PORT}` 占位符替换），执行 `python3 /opt/exp.py --target http://127.0.0.1:{PORT}`
7. **判分** — `exit(0)` = 漏洞仍在（修复失败）；`exit(1)` = 漏洞已封堵（修复成功，加分）

---

## 项目结构

```
awdp-platform/
├── app/                       # Flask 应用
│   ├── __init__.py            # 应用工厂 + 上下文处理器
│   ├── models.py              # 数据模型 (10 个模型)
│   ├── auth.py                # 注册/登录/密码修改
│   ├── main.py                # 选手端路由 (挑战/容器/防御)
│   ├── admin.py               # 管理员后台路由
│   ├── scoring.py             # AWDP 计分引擎
│   ├── forms.py               # WTForms 表单定义
│   └── docker_manager.py      # Docker SDK 封装
├── templates/                 # Jinja2 模板 (黑客风格)
├── static/                    # CSS / JS / 图片
│   └── css/custom.css        # 自定义黑客主题样式
├── challenges/                # 挑战题目 (Dockerfile + exp.py)
│   ├── _template/             # 出题模板
│   ├── sqli/                  # SQL 注入挑战
│   ├── ssrf/                  # SSRF 挑战
│   └── cc1/                   # Java CC1 反序列化挑战
├── services/
│   └── scheduler.py           # 后台调度服务
├── deploy/                    # Docker 部署文件 + 大屏后端
│   ├── Dockerfile             # 平台容器构建
│   ├── docker-compose.yml     # 编排文件
│   ├── save.sh                # 备份脚本
│   ├── load.sh                # 恢复部署脚本
│   ├── README.md              # 部署指南
│   └── asteroid-backend/      # 大屏可视化 Go WebSocket 后端
│       ├── main.go
│       ├── client.go
│       ├── model.go
│       ├── helper.go
│       ├── hub.go
│       ├── http.go
│       ├── team.txt
│       └── challenge.txt
├── scripts/                   # 辅助脚本
├── evaluate_defense.py        # 防御评估脚本
├── run.py                     # 入口 (init-db / run)
├── config.py                  # 配置
├── requirements.txt           # Python 依赖
├── .dockerignore              # Docker 构建排除
└── Asteroid-Unity/            # Unity 3D 大屏可视化项目
    └── Asteroid-master/
        └── Assets/
            ├── Scenes/Main.unity
            ├── Script/
            │   ├── MainController.cs
            │   ├── SinglePlanet.cs
            │   ├── RankItem.cs
            │   ├── TimeController.cs
            │   └── CameraRotate.cs
            ├── Prefab/
            │   ├── Planet.prefab
            │   └── RankItem.prefab
            └── Resources/
                └── Shield.png
```

### 数据模型

| 模型 | 说明 |
|------|------|
| `Team` | 队伍（选手实体，含积分） |
| `User` | 队员（可选，多成员队伍） |
| `Challenge` | 题目（配置 + 动态积分参数） |
| `Contest` | 比赛 |
| `ContestRound` | 比赛轮次 |
| `Container` | 容器实例（队伍 × 题目） |
| `Submission` | Flag 提交记录 |
| `Defense` | 防护包提交记录 |
| `ScoreLog` | 积分变更日志 |
| `CheckResult` | 容器健康检查结果 |
| `FlagHistory` | 历史 Flag 记录 |
| `SystemConfig` | 系统配置 |

---

## API 路由

### 选手端 (`/`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 首页（比赛列表） |
| GET | `/contest/<id>` | 比赛详情（含题目列表） |
| GET | `/challenge/<id>` | 题目详情 |
| POST | `/challenge/<id>/container/start` | 启动容器 |
| POST | `/challenge/<id>/container/stop` | 停止容器 |
| POST | `/challenge/<id>/container/reset` | 重置容器 |
| POST | `/challenge/<id>/container/refresh-flag` | 刷新 Flag |
| POST | `/challenge/<id>` | 提交 Flag |
| GET/POST | `/defend/<id>/upload` | 上传防护包 |
| GET | `/leaderboard` | 排行榜 |
| GET | `/leaderboard?contest_id=<id>` | 比赛排行榜 |
| GET | `/dashboard` | 队伍仪表盘 |

### 管理端 (`/admin`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/` | 管理后台首页 |
| GET/POST | `/admin/challenges/add` | 添加题目 |
| GET/POST | `/admin/challenges/<id>/edit` | 编辑题目 |
| GET | `/admin/teams` | 队伍列表 |
| POST | `/admin/teams/<id>/toggle-admin` | 切换管理员 |
| POST | `/admin/teams/<id>/reset-password` | 重置密码 |
| GET/POST | `/admin/contests` | 比赛管理 |
| POST | `/admin/contests/<id>/start` | 开始比赛 |
| POST | `/admin/contests/<id>/end` | 结束比赛 |
| GET/POST | `/admin/contests/<id>/rounds` | 轮次管理 |
| GET | `/admin/containers` | 容器监控 |
| GET | `/admin/defenses` | 防护包管理 |
| POST | `/admin/defenses/<id>/evaluate` | 触发评估 |
| GET | `/admin/export/scores.csv` | 导出成绩 |
| GET | `/admin/export/submissions.csv` | 导出提交记录 |

### 认证 (`/auth`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/auth/login` | 登录 |
| GET/POST | `/auth/register` | 注册 |
| GET/POST | `/auth/profile` | 资料/修改密码 |
| GET | `/auth/logout` | 登出 |

---

## 备份与迁移

### 创建备份（在 Windows 或 Linux 上）

```bash
bash deploy/save.sh
```

生成到 `backup/awdp-backup-<时间戳>/`:
```
backup/
├── source/              # 源码
├── images/              # Docker 镜像 (.tar)
├── database/awdp.db     # SQLite 数据库
└── uploads/             # 防御上传包
```

### 迁移到 Linux

```bash
# 1. 将整个项目目录传到 Linux
scp -r awdp-platform-main user@linux-server:/home/user/

# 2. 在 Linux 上恢复
cd awdp-platform-main
bash deploy/load.sh backup/awdp-backup-<时间戳>/

# 3. 访问 http://linux-server:5000
```

### 全新部署到 Linux

```bash
# 1. 安装 Docker
curl -fsSL https://get.docker.com | sh

# 2. 克隆代码、加载镜像
# 3. 启动
cd deploy
docker compose up -d --build
```

---

## 配置说明

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| `SECRET_KEY` | `SECRET_KEY` | `awdp-secret-key-...` | Flask 密钥，生产环境必改 |
| `DATABASE_URL` | `DATABASE_URL` | `sqlite:///awdp.db` | 数据库连接 |
| `PUBLIC_HOST` | `PUBLIC_HOST` | `127.0.0.1` | 容器对外地址 |

`config.py` 中可修改：
- `SQLALCHEMY_DATABASE_URI` — 更换为 MySQL/PostgreSQL
- `MAX_CONTENT_LENGTH` — 上传文件大小限制
- `WTF_CSRF_TIME_LIMIT` — CSRF 令牌有效期

### 后台调度服务

```bash
# 启动后台调度服务（健康检查 + 比赛轮次管理）
python -m services.scheduler
```

- 健康检查间隔：60 秒（容器宕机自动扣分）
- Flag 仅在容器启动/重置时注入，运行期间不自动刷新

---

## 小行星大屏可视化

项目附带基于 Unity 3D 的小行星（Asteroid）大屏可视化系统，用于 AWDP 比赛的实时战况展示。

### 架构

```
┌──────────────┐    WebSocket    ┌──────────────────┐
│  asteroid-   │ ──────────────> │  Unity 3D 大屏    │
│  backend     │    init/attack  │  (行星/战舰动画)   │
│  (Go/Gin)    │    /fix/rank    │                   │
│              │ <────────────── │  (连接)           │
│  19999/ws    │                 │  队伍外圈 + 题目内圈│
└──────┬───────┘                 └──────────────────┘
       │ HTTP
       ▼
┌──────────────┐
│  砺剑平台      │
│  (Flask)      │
│  5000         │
└──────────────┘
```

### 启动流程

```bash
# 1. 启动 AWDP 平台（确保有比赛在进行）
python run.py run

# 2. 启动 asteroid 后端（连接平台并推送 WebSocket 数据）
cd deploy/asteroid-backend
go run . --addr :19999

# 3. 生成队伍和题目数据
#    平台启动后运行客户端脚本（写入 team.txt / challenge.txt）
cd deploy/asteroid-backend
pip install requests
python ../../app/asteroid_client.py

# 4. 启动 Unity 大屏
#    打开 Asteroid-Unity/Asteroid-master/Assets/Scenes/Main.unity
#    → Unity Editor 播放
#    或直接运行构建出的可执行文件
```

> **注意**: Unity 项目使用 WebSocket 连接 `ws://localhost:19999/api/asteroid`，确保端口不被占用。

### 场景布局

- **外圈队伍行星**：10 个队伍均匀分布在半径 R=20 的圆上，代表各参赛队伍
- **内圈题目行星**：题目围绕中心分布在半径 R=4 的内圈上，代表待攻击的挑战目标
- **攻击动画**：队伍 → 题目（Break）或队伍 → 队伍（传统对抗），抛物线弹道 + 5 连发效果
- **修复动画**：题目 → 队伍（Fix），5 连发弹道 + 护盾展开（2.5 秒后收起）

### 可视化事件

| WebSocket 事件 | 效果 |
|----------------|------|
| `init` | 初始化所有行星位置、队伍信息、排行榜 |
| `attack` | 从发起方行星发射多枚炮弹到目标，目标标记为被攻陷 |
| `fix` | 从题目行星发射炮弹到队伍行星，目标弹起护盾 |
| `rank` | 更新排行榜和行星顶部排名显示 |
| `round` / `time` | 更新回合数与倒计时 |
| `status` | 设置队伍状态（down / attacked） |
| `easterEgg` | 触发陨石坠落彩蛋动画 |

### 队伍与题目配置

- `deploy/asteroid-backend/team.txt` — 队伍列表（每行: `队伍名,ID`）
- `deploy/asteroid-backend/challenge.txt` — 题目列表（每行: `题目名,ID`）

### 目录结构

```
deploy/asteroid-backend/       # Go WebSocket 后端
├── main.go                    # 入口 + 路由
├── client.go                  # WebSocket 客户端（连接 Flask 平台）
├── model.go                   # 数据结构
├── team.txt                   # 队伍配置
└── challenge.txt              # 题目配置

app/asteroid_client.py         # 平台数据同步脚本

Asteroid-Unity/Asteroid-master/ # Unity 3D 项目
├── Assets/
│   ├── Scenes/Main.unity      # 主场景
│   ├── Script/
│   │   ├── MainController.cs  # 核心控制（WebSocket、行星编排）
│   │   ├── SinglePlanet.cs    # 单个行星逻辑（护盾、状态、排名）
│   │   ├── RankItem.cs        # 排行榜行逻辑
│   │   ├── TimeController.cs  # 倒计时
│   │   └── CameraRotate.cs    # 摄像机旋转控制
│   ├── Prefab/
│   │   ├── Planet.prefab      # 行星预制体
│   │   └── RankItem.prefab    # 排行榜行预制体
│   └── Resources/
│       └── Shield.png         # 护盾贴图
└── ProjectSettings/
```
