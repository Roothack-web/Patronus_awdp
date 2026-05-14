# AWDP 自动化攻防演练平台

一个基于 Web 的自动化攻防演练（AWDP）竞赛平台，支持多队伍并发比赛、自动化防御评估、容器编排和 3D 可视化大屏。

## 功能

- 用户注册/登录、队伍管理
- Docker 容器编排（每队每题独立容器）
- 自动化防御评估引擎（上传补丁 → 构建环境 → 攻击验证 → 实时评分）
- 回合制比赛调度
- 动态 Flag 下发
- 实时排行榜
- 3D 可视化大屏集成（WebSocket 实时事件同步）
- Systemd 服务化部署

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python run.py --init-db

# 启动
python run.py
```

## 项目结构

```
awdp-platform-main/
├── app/                    # Flask 应用
│   ├── api/                # API 路由
│   ├── asteroid_client.py  # 大屏客户端
│   ├── docker_manager.py   # Docker 编排
│   ├── models.py           # 数据库模型
│   ├── scoring.py          # 评分逻辑
│   └── utils.py            # 工具函数
├── services/
│   └── scheduler.py        # 后台调度服务
├── deploy/
│   └── asteroid-backend/   # Go WebSocket 服务端
├── frontend/               # Vue 3 前端
├── challenges/             # 题目配置
├── config.py               # 配置
├── evaluate_defense.py     # 防御评估引擎
└── run.py                  # 入口
```

## 技术栈

- 后端: Python Flask + Gunicorn + SQLAlchemy
- 前端: Vue 3
- 容器: Docker SDK
- 可视化: Go/Gin WebSocket + Unity 3D
- 服务管理: systemd

## 致谢

- 3D 可视化大屏客户端基于 [05sec/Asteroid](https://github.com/05sec/Asteroid) (Apache 2.0)
- 原始平台框架基于 [ljnljn](https://github.com/ljnljn) (MIT)

## License

- 平台代码: MIT License
- asteroid-backend: Apache License 2.0
- 大屏客户端 (Unity): 请参见 [05sec/Asteroid](https://github.com/05sec/Asteroid)
