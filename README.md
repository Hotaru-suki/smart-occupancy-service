# 区域占用检测系统

> 基于 FastAPI 的区域占用检测与实时监控系统，覆盖后端开发、前端演示、认证鉴权、实时通信、自动化测试与持续集成。

## 项目定位

这个项目不是单纯的“测试工程样板”，也不是只做算法演示的 demo。它更接近一个完整的中小型业务系统原型，目标是把以下几件事放在同一个仓库里做好：

- 面向业务的后端能力：区域占用状态、事件记录、历史查询、管理员配置
- 面向演示的前端能力：登录注册、角色分离、实时状态、视频接入、管理员工作台
- 面向工程的保障能力：认证授权、Redis/MySQL 一致性、自动化测试、压测、CI

核心业务场景是：系统持续判断指定 ROI 区域内是否有人，并输出当前人数、占用状态、占用时长、进入/离开事件，供前端实时展示和后台查询。

## 核心能力

### 业务能力

- 支持真实模式与 Mock 模式两套运行路径
- 支持 ROI 区域配置与后台更新
- 支持占用状态、人数、占用时长、日统计输出
- 支持进入/离开事件记录、最近事件查询、历史事件查询
- 支持 WebRTC 视频接入

### 平台能力

- 登录、注册、会话管理、密码修改
- `viewer / admin` 两级权限控制
- WebSocket 实时状态推送
- Redis 缓存与 MySQL 持久化
- 管理员用户管理：改角色、删用户、批量清理测试账号

### 工程能力

- `pytest + Allure` 自动化测试
- JMeter 压测场景
- Jenkins Pipeline
- WebSocket 实时烟测
- Redis / MySQL 一致性验证
- 参数化异常测试、错误请求方法测试、并发写读测试

## 技术栈

### 后端

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Redis
- MySQL

### 识别与实时能力

- OpenCV
- Ultralytics YOLOv8
- aiortc
- WebSocket

### 前端

- 原生 HTML / CSS / JavaScript

### 测试与 CI

- pytest
- Allure
- Apache JMeter
- Jenkins

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

## 关键文档

- [系统架构说明](./docs/ARCHITECTURE.md)
- [API 说明](./docs/API_REFERENCE.md)
- [版本演进说明](./docs/CHANGELOG.md)
- [认证与注册规则](./docs/AUTH_RULES.md)
- [测试用例设计](./docs/TEST_CASES.md)
- [测试报告说明](./docs/TEST_REPORT.md)

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

## 快速启动

### 1. 启动依赖

```bash
docker compose up -d
```

### 2. 配置环境变量

复制 `.env.example` 并按实际环境修改 `.env`。  
本地默认示例配置和认证规则已经写在 `.env.example` 注释中。

### 3. 启动服务

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 4. 打开前端

```text
http://127.0.0.1:8000/ui/
```

## 开发与测试并重的展示点

这个项目目前更适合这样理解：

- 从开发视角看，它已经具备典型业务系统的基础骨架：鉴权、权限、配置管理、实时通信、前后端联动
- 从测试视角看，它又覆盖了接口自动化、异常输入、并发、缓存一致性、压测与 CI

也就是说，这个仓库的价值不只是“我写了测试”，而是“我把一个可运行的业务原型和一套可验证的质量体系放在了一起”。

## 后续可继续增强的方向

- 增加正式的 OpenAPI 补充文档和示例请求体
- 把前端管理台继续拆成更清晰的模块
- 补 WebSocket / WebRTC 端到端运行验证
- 继续细化缓存故障、数据库故障、回源压力专项测试
