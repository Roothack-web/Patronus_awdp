# 砺剑AWDp — 完整部署文档

## 系统架构

```
┌──────────────────────────────────────────────────────────────────┐
│                        全套系统组件                                 │
│                                                                  │
│  ┌─────────────────────────┐      ┌─────────────────────────┐   │
│  │   AWDP 平台 (Flask)     │      │  asteroid-backend (Go)  │   │
│  │   :5000                 │─────>│  :8080 / :19999         │   │
│  │   Web 管理后台           │ HTTP │  WebSocket 中转服务      │   │
│  │   Docker 容器管理        │      │  推送 init/attack/fix   │   │
│  │   计分引擎               │      │  队伍/题目配置           │   │
│  └──────────┬──────────────┘      └──────────┬──────────────┘   │
│             │                                │ WebSocket         │
│             ▼                                ▼                   │
│  ┌──────────────────┐       ┌─────────────────────────┐         │
│  │ Docker 容器集群    │       │  Unity 3D 大屏           │         │
│  │ 每队伍×每题目=1容器 │       │  行星可视化 + 动画        │         │
│  │ 动态 Flag 注入    │       │  排行榜 + 状态           │         │
│  └──────────────────┘       └─────────────────────────┘         │
└──────────────────────────────────────────────────────────────────┘
```

系统由三个核心组件构成：

| 组件 | 技术栈 | 端口 | 说明 |
|------|--------|------|------|
| **AWDP 平台** | Python Flask + Docker | 5000 | 比赛管理、计分、容器编排 |
| **asteroid-backend** | Go (Gin + Gorilla WebSocket) | 8080 / 19999 | 接收平台事件，WebSocket 推送大屏 |
| **Unity 大屏** | Unity 3D + BestHTTP WebSocket | — | 3D 行星战况可视化 |

数据流：Flask 平台 (scoring.py / main.py) → HTTP POST → asteroid-backend → WebSocket 广播 → Unity 大屏

---

## 目录

- [系统架构](#系统架构)
- [一、环境要求](#一环境要求)
- [二、构建挑战镜像](#二构建挑战镜像)
- [三、部署 AWDP 平台](#三部署-awdp-平台)
- [四、部署 asteroid-backend](#四部署-asteroid-backend)
- [五、启动 Unity 大屏](#五启动-unity-大屏)
- [六、完整启动流程](#六完整启动流程)
- [七、备份与迁移](#七备份与迁移)
- [八、配置参考](#八配置参考)
- [九、常见问题](#九常见问题)

---

## 一、环境要求

### 基础环境

| 依赖 | 版本要求 | 用途 |
|------|----------|------|
| Python | ≥ 3.9 | AWDP 平台运行 |
| Docker | ≥ 20.10 | 容器管理与防御评估 |
| Go | ≥ 1.21 | 编译 asteroid-backend |
| Unity | 2019.4+ | 大屏可视化（仅开发/调试需要） |

### 端口占用

| 端口 | 组件 | 说明 |
|------|------|------|
| 5000 | AWDP 平台 | Web 管理界面 |
| 8080 | asteroid-backend (Docker) | HTTP API + WebSocket |
| 19999 | asteroid-backend (本地) | 独立运行时的端口 |
| 3xxxx | 挑战容器 | Docker 动态映射，每容器独立端口 |

---

## 二、构建挑战镜像

每个挑战对应一个 Docker 镜像，提供漏洞环境。

### 标准出题模板

```
challenges/_template/
├── Dockerfile          # php:8.1-apache 基础镜像
├── build.sh            # 构建脚本
├── exploit.sh          # 防御评估 EXP (容器内执行)
└── web/
    ├── index.php       # 漏洞入口文件
    └── start.sh        # 容器启动脚本 (写 FLAG, 启服务)
```

### 构建命令

```bash
# 进入挑战目录
cd challenges/sqli
./build.sh awdp-sqli

cd challenges/ssrf
./build.sh awdp-ssrf
```

构建后可用 `docker images` 验证：

```
REPOSITORY    TAG       IMAGE ID       CREATED          SIZE
awdp-sqli     latest    a1b2c3d4e5f6   10 seconds ago   458MB
awdp-ssrf     latest    b2c3d4e5f6a7   20 seconds ago   462MB
```

### 挑战约定

| 约定 | 说明 |
|------|------|
| `$FLAG` 环境变量 | 平台创建容器时注入，`start.sh` 负责写入 `/flag` |
| `/flag` 文件 | PHP 代码通过 `file_get_contents('/flag')` 读取 |
| `exploit.sh` | 位于 `challenges/<镜像名>/exploit.sh`，评估系统自动查找 |
| 镜像命名 | `awdp-<题目名>` 前缀，评估系统据此定位 exploit 脚本 |

---

## 三、部署 AWDP 平台

### 方式 A：本地运行（开发/调试）

```bash
# 1. 进入项目目录
cd awdp-platform-main

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate      # Linux
# venv\Scripts\activate       # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库（自动创建管理员 admin / admin）
python run.py init-db

# 5. 启动平台
python run.py run

# 6. （可选）启动后台调度服务
python -m services.scheduler
```

访问 http://localhost:5000

### 方式 B：Docker 部署（生产）

```bash
# 1. 确保挑战镜像已构建
docker images | grep awdp-

# 2. 启动全部服务
cd deploy
docker compose up -d --build

# 3. 查看日志
docker compose logs -f
```

#### Docker Compose 服务说明

`docker-compose.yml` 定义了两个服务：

| 服务名 | 容器名 | 说明 |
|--------|--------|------|
| `platform` | `awdp-platform` | Flask Web 应用，含 Docker 管理能力 |
| `asteroid-backend` | `awdp-asteroid` | Go WebSocket 服务，推送给大屏 |

验证启动：

```bash
docker compose ps
```

输出示例：

```
NAME              IMAGE                        STATUS        PORTS
awdp-platform     deploy-platform              Up (healthy)  0.0.0.0:5000->5000/tcp
awdp-asteroid     deploy-asteroid-backend      Up           0.0.0.0:8080->8080/tcp
```

### 初始化配置

管理员登录后需完成：

1. **创建比赛** — `/admin/contests` → 添加比赛，设置起止时间
2. **添加题目** — `/admin/challenges/add` → 绑定 Docker 镜像、端口映射
3. **管理轮次** — `/admin/contests/<id>/rounds` → 添加时间轮次
4. **选手注册** — 队伍注册后即可开始比赛

---

## 四、部署 asteroid-backend

asteroid-backend 是 AWDP 平台与 Unity 大屏之间的 WebSocket 中转服务。

### 方式 A：本地运行

```bash
# 1. 进入后端目录
cd deploy/asteroid-backend

# 2. 确保队伍和题目配置存在
#    可由平台自动生成，或手动创建
cat team.txt      # 格式: 队伍名,ID
cat challenge.txt # 格式: 题目名,ID

# 3. 启动服务
go run . --addr :19999
```

### 方式 B：编译后运行

```bash
cd deploy/asteroid-backend
go build -o asteroid-backend .
./asteroid-backend --addr :19999
```

### 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--addr` | `:19999` | 监听地址和端口 |
| `--title` | `"砺剑AWDp"` | 大屏标题 |
| `--token` | `""` | 认证令牌（与平台 `ASTEROID_TOKEN` 一致） |

### 数据文件

| 文件 | 格式 | 说明 |
|------|------|------|
| `team.txt` | `队伍名,ID` (每行) | 队伍列表 |
| `challenge.txt` | `题目名,ID` (每行) | 题目列表 |

数据文件可由 `app/asteroid_client.py` 自动从平台同步生成：

```bash
cd deploy/asteroid-backend
python ../../app/asteroid_client.py
```

### REST API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/teams` | 查看队伍列表 |
| GET | `/api/challenges` | 查看题目列表 |
| WS | `/api/asteroid` | WebSocket 大屏推送 |

### Docker 方式运行

在 Docker Compose 中已包含，也可单独运行：

```bash
cd deploy/asteroid-backend
docker build -t awdp-asteroid-backend .
docker run -d -p 8080:8080 \
  -v /path/to/team.txt:/app/team.txt \
  -v /path/to/challenge.txt:/app/challenge.txt \
  awdp-asteroid-backend
```

### 平台集成配置

平台通过环境变量连接 asteroid-backend：

```bash
export ASTEROID_URL=http://127.0.0.1:8080
export ASTEROID_TOKEN=your-secret-token
```

平台在以下时机自动推送事件：

| 事件 | 触发时机 | 数据来源 |
|------|----------|----------|
| `break` | 选手提交正确 Flag | `scoring.py` |
| `fix` | 防御评估成功 | `scoring.py` |
| `rank` | 积分变更 | `scoring.py` |
| `status` | 容器上下线 | `main.py` |

---

## 五、启动 Unity 大屏

### 前置条件

- Unity 2019.4.22f1 或更高版本
- WebSocket 连接地址: `ws://<asteroid-backend-ip>:<port>/api/asteroid`

### 启动方式

**方式 A：Unity Editor 运行**

1. 用 Unity 打开 `Asteroid-Unity/Asteroid-master/`
2. 打开场景 `Assets/Scenes/Main.unity`
3. 配置连接地址（代码中已默认配置）
4. 点击播放按钮

**方式 B：构建可执行文件**

```bash
# 在 Unity 中:
# File → Build Settings → PC, Mac & Linux Standalone
# → Scenes/Main → Build
```

### 配置

大屏连接地址在 `Assets/StreamingAssets/asteroid.ini` 中配置：

```ini
[connect]
url = ws://localhost:19999/api/asteroid
image_url = http://localhost:19999/api/uploads/

[scene]
radius = 20
```

### 场景布局

- **外圈**：队伍行星，R=20 均匀分布
- **内圈**：题目行星，R=4（R/5）均匀分布，角度偏移半个队伍间隔
- **中心**：比赛标题与倒计时

### 可视化事件

| WebSocket 事件 | 效果 |
|----------------|------|
| `init` | 初始化所有行星位置、队伍信息、排行榜 |
| `attack` | 从发起方行星发射 5 枚抛物线炮弹到目标 |
| `fix` | 从题目行星发射 5 枚炮弹到队伍，目标弹起护盾 (2.5s) |
| `rank` | 更新排行榜和行星顶部排名 |
| `round` / `time` | 更新回合数与倒计时 |
| `status` | 设置队伍状态（down / attacked） |
| `clear` / `clearAll` | 清除队伍状态 |
| `easterEgg` | 触发陨石坠落彩蛋动画 |

---

## 六、完整启动流程

以下是从零开始部署一套完整 AWDP 比赛系统的步骤。

### 步骤概览

```
构建镜像 → 启动平台 → 创建比赛 → 启动 asteroid → 同步数据 → 启动大屏
```

### 详细步骤

```bash
# ─── Step 1: 构建挑战镜像 ───────────────────────────────────
cd challenges/sqli && ./build.sh awdp-sqli
cd challenges/ssrf && ./build.sh awdp-ssrf

# ─── Step 2: 启动 AWDP 平台 ─────────────────────────────────
cd awdp-platform-main
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python run.py init-db
python run.py run &
# 或 Docker 方式:
# cd deploy && docker compose up -d --build

# ─── Step 3: 管理员后台配置（首次需手动完成） ─────────────
# 浏览器打开 http://localhost:5000
# 登录 admin / admin
# → 创建比赛
# → 添加题目 (awdp-sqli, awdp-ssrf)
# → 管理轮次

# ─── Step 4: 启动 asteroid-backend ──────────────────────────
cd deploy/asteroid-backend
go run . --addr :19999 &
# 或 Docker 方式已在 docker compose 中包含

# ─── Step 5: 同步队伍和题目数据 ────────────────────────────
python ../../app/asteroid_client.py

# ─── Step 6: 启动 Unity 大屏 ───────────────────────────────
# 打开 Unity Editor → 播放 Main.unity
# 或运行构建出的可执行文件
```

### 验证状态

```
# 验证平台
curl http://localhost:5000
# → 返回 HTML 首页

# 验证 asteroid-backend
curl http://localhost:8080/api/teams
# → JSON 队伍列表

# 验证 WebSocket
# 使用浏览器或 wscat 连接 ws://localhost:19999/api/asteroid
# → 收到 init 消息包含队伍和题目数据
```

---

## 七、备份与迁移

### 创建备份

```bash
bash deploy/save.sh
```

生成到 `backup/awdp-backup-<时间戳>/`：

```
backup/
├── source/              # 源码（排除 venv/__pycache__）
├── images/              # Docker 镜像 (.tar)
│   ├── awdp-sqli_latest.tar
│   └── awdp-ssrf_latest.tar
├── database/awdp.db     # SQLite 数据库
└── uploads/             # 选手上传的防护包
```

### 迁移到 Linux 服务器

```bash
# 1. 将备份目录传到 Linux
scp -r awdp-platform-main user@linux-server:/home/user/

# 2. 在 Linux 上恢复
cd awdp-platform-main
bash deploy/load.sh backup/awdp-backup-<时间戳>/

# 3. 验证服务
curl http://linux-server:5000
docker compose ps
```

`load.sh` 自动完成：加载 Docker 镜像 → 恢复数据库 → 启动 docker compose

### 手动迁移（不依赖 load.sh）

```bash
# 加载镜像
for img in backup/awdp-backup-*/images/*.tar; do docker load -i "$img"; done

# 恢复数据库
cp backup/awdp-backup-*/database/awdp.db .

# 恢复上传
cp -r backup/awdp-backup-*/uploads/* instance/uploads/

# 启动
cd deploy && docker compose up -d --build
```

---

## 八、配置参考

### 平台配置 (`config.py` / 环境变量)

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| `SECRET_KEY` | `SECRET_KEY` | `awdp-secret-key-...` | Flask 密钥，生产环境必改 |
| `DATABASE_URL` | `DATABASE_URL` | `sqlite:///awdp.db` | 数据库连接（可换 PostgreSQL） |
| `PUBLIC_HOST` | `PUBLIC_HOST` | `127.0.0.1` | 容器对外映射地址 |
| — | `ASTEROID_URL` | `http://127.0.0.1:8080` | asteroid-backend 地址 |
| — | `ASTEROID_TOKEN` | — | 大屏认证令牌 |
| — | `ASTEROID_TOKEN_FILE` | `asteroid_token.txt` | 令牌文件路径 |
| — | `TEAMDATA_DIR` | — | 队伍数据目录（Docker 共享卷） |

### asteroid-backend 配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--addr` | `:19999` | 监听地址 |
| `--port` | `19999` | 端口（Docker 版使用） |
| `--title` | `"砺剑AWDp"` | 大屏标题 |
| `--token` | `""` | 认证令牌 |

### Docker Compose 环境变量

在 `.env` 文件中配置：

```ini
PUBLIC_HOST=192.168.1.100
SECRET_KEY=your-strong-secret-key-here
ASTEROID_TOKEN=your-asteroid-secret-token
```

### 大屏 Unity 配置

`Assets/StreamingAssets/asteroid.ini`:

```ini
[connect]
url = ws://localhost:19999/api/asteroid
image_url = http://localhost:19999/api/uploads/

[scene]
radius = 20
```

---

## 九、常见问题

### 容器无法启动

```bash
# 查看平台日志
docker compose logs platform

# 检查 Docker 是否可用
docker ps

# 确认镜像存在
docker images | grep awdp-
```

### 大屏连接不上

```
# 1. 确认 asteroid-backend 运行中
curl http://localhost:8080/api/teams

# 2. 检查 WebSocket 地址
# Unity 配置中的 url 必须与 asteroid-backend --addr 一致

# 3. 防火墙放行端口
# Windows: netsh advfirewall firewall add rule name="AWDP" dir=in action=allow protocol=tcp localport=5000,8080,19999
```

### 排行榜中文乱码

Unity UI.Text 组件对中文字体支持有限。解决方式：

1. 在 Unity 中选中中文字体文件，Inspector → **Character Set** 改为 **Dynamic**
2. 或替换排行榜预制体的文本组件为 TextMeshPro

### 备份恢复后数据不完整

```bash
# 检查备份目录结构
ls -la backup/awdp-backup-*/

# 缺少某个部分可手动补充:
# 镜像: 重新 docker build
# 数据库: 从旧备份恢复
```

### 常用 Docker 命令

```bash
docker compose logs -f        # 实时日志
docker compose down           # 停止服务
docker compose restart        # 重启
docker compose ps             # 查看状态
docker system prune -f        # 清理未使用资源
```
