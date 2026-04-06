# 区域占用检测系统

> 基于 FastAPI 的区域占用检测与实时监控系统，覆盖业务接口、实时链路、认证鉴权、自动化测试与持续集成。

## 项目概览

这个仓库不是单纯的算法 demo，也不是只展示测试框架的样板项目。它更接近一个可运行、可验证、可持续演进的中小型业务系统原型，核心目标包括：

- 业务能力：区域占用状态、人数统计、进入离开事件、历史查询、管理员配置
- 实时能力：WebSocket 状态推送、WebRTC 视频接入、真实模式与 Mock 模式
- 工程能力：会话认证、权限控制、Redis/MySQL、一致性校验、自动化测试、压测、Jenkins

当前版本为 `v0.7`。

## 核心能力

- 支持真实模式与 Mock 模式两套运行路径
- 支持 ROI 区域配置和后台更新
- 支持状态、人数、占用时长、日统计输出
- 支持进入/离开事件、最近事件、历史事件查询
- 支持登录、注册、会话管理、密码修改
- 支持 `viewer / admin` 两级权限控制
- 支持 WebSocket 实时推送和 WebRTC 视频接入
- 支持 Redis 缓存与 MySQL 持久化
- 支持 `pytest + Allure`、JMeter、Jenkins Pipeline

## 技术栈

- 后端：Python、FastAPI、Pydantic、SQLAlchemy
- 基础设施：MySQL、Redis
- 识别与实时：OpenCV、Ultralytics YOLOv8、aiortc、WebSocket
- 前端：原生 HTML / CSS / JavaScript
- 测试与 CI：pytest、Allure、Apache JMeter、Jenkins

## 项目结构

```text
app/
├─ api/               路由层
├─ core/              ROI、视频帧缓冲等基础能力
├─ infrastructure/    数据库、缓存、日志、队列、仓储
├─ runtime/           真实计数器 / Mock 计数器
├─ security/          认证、会话、密码处理
├─ services/          业务服务层
├─ config.py          配置
├─ main.py            应用入口
└─ schemas.py         请求响应模型

frontend/             同源前端页面
tests/                自动化测试
jmeter/               压测场景
scripts/              脚本工具
docs/                 关键文档
```

## 环境文件约定

- `.env.example`：模板文件，只描述需要哪些配置，不写真实本地值
- `.env.dev`：本地开发使用的真实配置
- `.env.test`：本地测试使用的真实配置
- `.env.test.example`：Jenkins / SCM 模式使用的测试模板
- `.env`：应用运行时实际读取的环境文件

推荐使用方式：

```bash
cp .env.dev .env
```

如果是 Jenkins 流水线：

- 流水线会基于 `.env.test.example` 和 Jenkins 环境变量生成 `.env`
- 后续统一从 `.env` 读取运行配置

## 本地开发启动

### 1. 启动依赖服务

```bash
docker compose up -d
```

当前 `docker-compose.yml` 会启动：

- Redis
- MySQL

### 2. 准备环境文件

首次使用可以先参考模板：

```bash
cp .env.example .env
```

本地开发更推荐直接使用开发配置：

```bash
cp .env.dev .env
```

### 3. 安装依赖

只运行服务：

```bash
pip install -r requirements.txt
```

开发与测试：

```bash
pip install -r requirements-dev.txt
```

### 4. 启动后端

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 5. 打开前端

访问：

```text
http://127.0.0.1:8000/ui/
```

## 测试执行

使用测试环境配置时，推荐先复制：

```bash
cp .env.test .env
```

然后执行：

```bash
pytest tests
```

如果要生成 Allure 结果：

```bash
pytest tests --alluredir=allure-results
```

## 部署与集成说明

推荐按三条链路理解：

- 本地开发：`docker compose up -d` + `.env.dev` + `uvicorn`
- 本地测试：`.env.test` + `pytest`
- Jenkins 集成：流水线基于 `.env.test.example` 和 Jenkins 环境变量生成 `.env`，然后执行依赖安装、服务启动、烟测、pytest 和 JMeter

更完整的部署操作说明见：

- [部署与运行说明](./docs/DEPLOYMENT.md)

## 当前接口概览

### 公开接口

- `GET /`
- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/session`
- `GET /ui/`

### 登录后接口

- `GET /api/status`
- `POST /api/webrtc-offer`
- `PATCH /api/auth/password`
- `POST /api/auth/logout`
- `WS /api/realtime`

### 管理员接口

- `GET /api/events`
- `GET /api/history/events`
- `GET /api/admin/users`
- `PATCH /api/admin/users/{username}/role`
- `DELETE /api/admin/users/{username}`
- `DELETE /api/admin/users`
- `GET /api/admin/regions/default`
- `PUT /api/admin/regions/default/roi`

## 关键文档

- [系统架构说明](./docs/ARCHITECTURE.md)
- [API 说明](./docs/API_REFERENCE.md)
- [部署与运行说明](./docs/DEPLOYMENT.md)
- [版本演进说明](./docs/CHANGELOG.md)
- [认证与注册规则](./docs/AUTH_RULES.md)
- [测试用例设计](./docs/TEST_CASES.md)
- [测试报告说明](./docs/TEST_REPORT.md)

## 项目价值

这个仓库的价值不只是“有一套测试”，而是把一个可运行的业务原型和一套可验证的工程保障放在了一起：

- 从开发视角看，它具备典型业务系统的基础骨架
- 从测试视角看，它覆盖了接口、异常输入、并发、缓存一致性、压测和 CI

## 后续可继续增强的方向

- 补充更细的 OpenAPI 示例与接口约束说明
- 继续拆分前端管理台模块
- 补 WebSocket / WebRTC 端到端运行验证
- 继续细化缓存故障、数据库故障、回源压力专项测试
