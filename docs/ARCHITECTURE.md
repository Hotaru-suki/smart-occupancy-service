# 系统架构说明

## 1. 架构目标

本系统围绕“区域占用检测”这一业务目标，构建了一套包含实时识别、状态查询、事件记录、权限控制、前端展示和测试保障的完整工程结构。

整体设计目标有三点：

- 业务链路清晰：从计数器到缓存、数据库、接口、前端形成闭环
- 结构可维护：路由、服务、仓储、运行时职责分离
- 测试可落地：支持 Mock 模式、自动化测试和压测

## 2. 分层结构

### 路由层 `app/api`

负责：

- 暴露 HTTP / WebSocket 接口
- 处理权限依赖
- 接收参数并调用 service

不负责：

- 直接编排复杂业务
- 在路由内写大量缓存回退或序列化逻辑

### 服务层 `app/services`

负责：

- 业务逻辑编排
- 缓存回退
- 响应模型拼装
- 跨仓储协调

当前代表性服务：

- `AuthService`
- `AdminService`
- `MonitoringService`
- `HistoryService`

### 仓储层 `app/infrastructure/repositories`

负责：

- MySQL 持久化访问
- 查询与更新封装
- 与具体 ORM 细节解耦

### 运行时层 `app/runtime`

负责：

- 真实识别循环或 Mock 时间线驱动
- 占用状态计算
- 事件生成
- Redis 状态缓存刷新

### 安全层 `app/security`

负责：

- 会话读取与校验
- Cookie 设置
- 密码哈希与校验
- 权限依赖

## 3. 核心运行链路

### 3.1 状态链路

1. `PeopleCounter` 或 `MockPeopleCounter` 产生当前状态
2. 状态快照写入 Redis `occupancy:status`
3. `MonitoringService.get_status()` 优先读 Redis
4. Redis 不可用时回退到运行时计数器
5. `/api/status` 返回给前端

### 3.2 事件链路

1. 运行时识别到进入 / 离开事件
2. 事件写入内存列表并通过 `event_service` 投递
3. 异步 worker 将事件写入 Redis 与 MySQL
4. `MonitoringService.get_events()` 优先读 Redis
5. `/api/events` 向管理员返回最近事件

### 3.3 实时链路

1. 前端登录后先拉一次 `/api/status`
2. 管理员额外拉取 `/api/events` 与管理数据
3. 前端建立 `/api/realtime` WebSocket
4. 后端按周期推送状态
5. 管理员连接额外接收事件推送

### 3.4 权限链路

1. 登录后服务端创建 HttpOnly Cookie 会话
2. 每次请求从 Redis 会话中读取用户名
3. 再从数据库获取当前角色，避免旧 session 角色失真
4. `viewer` 拥有只读能力
5. `admin` 拥有管理写能力

## 4. Mock 模式的价值

Mock 模式不是简单占位，而是工程化设计的重要组成部分：

- 降低对摄像头、模型、真实流媒体环境的依赖
- 让自动化测试和 CI 结果更稳定
- 让前后端联调不必依赖完整识别链路
- 便于把问题定位在接口、权限、缓存、数据库还是运行时逻辑

## 5. 当前的性能优化点

- 状态读取优先走 Redis
- WebSocket 对普通用户不计算事件负载
- `daily_stats` 落库增加节流窗口
- 高频接口的读逻辑已下沉到 `MonitoringService`，便于后续集中优化

## 6. 当前的可维护性设计

- 认证、管理、监控、历史查询职责分层
- 接口测试大量使用参数化和公共 helper
- 用户管理支持单删和批量清理测试账号
- 关键认证与测试规则文档化

## 7. 仍可继续优化的点

- 进一步抽象统一的缓存访问组件
- 为 WebSocket 和 WebRTC 增加更完整的端到端测试
- 增加更细粒度的指标采集和 tracing
- 补充更正式的部署文档与运维手册
