# 测试用例设计说明

## 1. 文档目的

本文档用于说明 `api` 项目的自动化测试用例设计思路、覆盖范围、验证点与执行方式

## 2. 测试目标

本项目测试重点为：

1. 验证核心接口的可用性和返回结构正确性
2. 验证状态、事件等关键业务字段的基本逻辑
3. 验证接口结果与 Redis / MySQL 数据的一致性
4. 验证系统在持续集成环境中的可重复执行能力
5. 验证关键接口在不同并发下的性能表现与拐点区间

## 3. 功能自动化测试用例清单

### 3.0 Auth API

| 用例编号 | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| AUTH-001 | 公共登录入口校验 | 服务已启动 | POST `/api/auth/login` | 不区分用户/管理员页面，返回 200 并写入 Cookie |
| AUTH-002 | 用户注册成功校验 | 服务已启动 | POST `/api/auth/register`，`role=viewer` | 返回 201，用户创建成功 |
| AUTH-003 | 管理员注册成功校验 | 服务已启动 | POST `/api/auth/register`，`role=admin` 且携带注册码 | 返回 201，管理员创建成功 |
| AUTH-004 | 注册幂等性校验 | 同一用户名和密码重复提交 | 重复 POST `/api/auth/register` | 第二次返回 200 且 `created=false` |
| AUTH-005 | 登录失败与角色不匹配校验 | 服务已启动 | 使用错误密码或错误角色 POST `/api/auth/login` | 返回 401 或 403 |
| AUTH-006 | 会话状态查询校验 | 已完成登录 | GET `/api/auth/session` | 返回 `authenticated=true`，角色与账号一致 |
| AUTH-007 | 受保护接口鉴权校验 | 未登录 | GET `/api/status` | 返回 401 |
| AUTH-008 | 自助修改密码校验 | 用户或管理员已登录 | PATCH `/api/auth/password` | 当前密码正确时返回 200，新密码生效 |
| AUTH-009 | 认证边界与注入输入校验 | 服务已启动 | 对用户名/密码传入异常值、注入值、超长值 | 返回 401 / 409 / 422，且接口不崩溃 |
| AUTH-010 | 登录失败限流校验 | 服务已启动 | 对同一来源和用户名连续多次错误登录 | 达到阈值后返回 429 |
| AUTH-011 | 公开/受保护接口重定向校验 | 服务已启动 | 对公开接口和未登录受保护接口禁用跳转访问 | 不返回 3xx 重定向 |

### 3.0.1 UI Shell

| 用例编号 | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| UI-001 | 登录页优先展示校验 | 服务已启动 | GET `/ui/` | 登录表单可见，注册表单与业务台默认隐藏 |
| UI-002 | 注册模式切换入口校验 | 服务已启动 | GET `/ui/` | 页面包含普通用户注册、管理员注册和管理员注册码字段 |

### 3.0.2 HTTP Method

| 用例编号 | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| METHOD-001 | 错误请求方法拦截校验 | 服务已启动 | 对主要接口使用错误 HTTP Method 访问 | 返回 405，且不发生重定向 |

### 3.1 Root API

| 用例编号 | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| ROOT-001 | 根接口状态码校验 | 服务已启动 | GET `/` | 返回 200 |
| ROOT-002 | 根接口结构校验 | 服务已启动 | GET `/` | 包含 `service/version/mock/supports_video` 等字段，字段类型正确 |

### 3.2 Health API

| 用例编号 | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| HEALTH-001 | 健康接口状态码校验 | 服务已启动 | GET `/api/health` | 返回 200 |
| HEALTH-002 | 健康接口结构校验 | 服务已启动 | GET `/api/health` | 返回字段完整，布尔和时间字段类型正确 |
| HEALTH-003 | health/status 环境一致性校验 | 服务已启动 | 分别请求 `/api/health` 与 `/api/status` | `mock/supports_video/running/camera_ok/detector_ok` 保持一致 |

### 3.3 Status API

| 用例编号 | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| STATUS-001 | 状态接口状态码校验 | 服务已启动 | GET `/api/status` | 返回 200 |
| STATUS-002 | 状态接口结构校验 | 服务已启动 | GET `/api/status` | 字段齐全，类型正确 |
| STATUS-003 | 状态接口基础业务逻辑校验 | 服务已启动 | GET `/api/status` | `status/current_people/occupied_duration_sec` 等逻辑自洽 |
| STATUS-004 | 根接口与状态接口一致性校验 | 服务已启动 | GET `/` 与 GET `/api/status` | `mock/supports_video` 一致 |
| STATUS-005 | 状态接口与缓存一致性校验 | Redis 正常 | 请求 `/api/status` 后读取 `occupancy:status` | 关键字段一致 |
| STATUS-006 | 状态接口 POST 非法方法校验 | 服务已启动 | POST `/api/status` | 返回 405 或 422 |
| STATUS-007 | mock 模式视频能力校验 | mock 模式开启 | GET `/api/status` | `mock=true` 且 `supports_video=false` |

### 3.4 Events API

| 用例编号 | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| EVENTS-001 | 事件接口状态码校验 | 服务已启动 | GET `/api/events?limit=10` | 返回 200 |
| EVENTS-002 | 事件接口结构校验 | 服务已启动 | GET `/api/events?limit=10` | 返回 `mock` 和 `events`，每条事件结构正确 |
| EVENTS-003 | limit=5 数量校验 | 服务已启动 | GET `/api/events?limit=5` | 返回事件数量不超过 5 |
| EVENTS-004 | limit 边界值校验 | 服务已启动 | GET `/api/events?limit=1/20/100` | 返回数量合法 |
| EVENTS-005 | limit 异常参数校验 | 服务已启动 | GET `/api/events?limit=0/101/-1/abc/1.5` | 返回 422 |
| EVENTS-006 | 默认 limit 返回结构校验 | 服务已启动 | GET `/api/events` | 返回标准结构，事件数组元素结构正确 |

### 3.4.1 History API

| 用例编号 | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| HISTORY-001 | 历史接口状态码校验 | 服务已启动 | GET `/api/history/events?limit=10` | 返回 200 |
| HISTORY-002 | 历史查询参数注入校验 | 服务已启动 | 对 `region_name/event_type/limit` 传入注入与异常参数 | 返回 200 或 422，接口不崩溃 |

### 3.4.2 Admin API / RBAC

| 用例编号 | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| ADMIN-001 | viewer 权限限制校验 | viewer 已登录 | 访问 `/api/admin/users`、`/api/history/events`、`/api/events` | 返回 403 |
| ADMIN-002 | admin 用户列表查看校验 | admin 已登录 | GET `/api/admin/users` | 返回 200 |
| ADMIN-003 | admin 用户角色修改校验 | admin 已登录 | PATCH `/api/admin/users/{username}/role` | 返回 200 |
| ADMIN-004 | admin ROI 写权限校验 | admin 已登录 | PUT `/api/admin/regions/default/roi` | 返回 200 |
| ADMIN-005 | 多 admin 并发写 ROI 校验 | 至少两个 admin 会话 | 同时更新 ROI | 请求成功，最终 ROI 为某次有效提交，数据不损坏 |
| ADMIN-006 | admin 写 / viewer 读并发校验 | admin 与 viewer 同时在线 | admin 更新 ROI，viewer 同时读取 `/api/status` | 读写均成功，读接口不崩溃 |

### 3.5 Redis Cache

| 用例编号 | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| REDIS-001 | 状态缓存存在性校验 | Redis 正常 | 请求 `/api/status` 后检查 `occupancy:status` | key 存在 |
| REDIS-002 | 状态缓存结构校验 | Redis 正常 | 请求 `/api/status` 后读取缓存 | 缓存结构完整 |
| REDIS-003 | 状态缓存与接口一致性校验 | Redis 正常 | 比较接口返回与缓存内容 | 关键字段一致 |
| REDIS-004 | 事件缓存可读性校验 | Redis 正常 | 请求 `/api/events` 并读取 `occupancy:events` | 缓存可解析、结构正确 |
| REDIS-005 | 事件缓存与接口一致性校验 | Redis 正常 | 比较接口事件与缓存事件 | event/people_count 一致 |
| REDIS-006 | 测试专用缓存 key 写读校验 | Redis 正常 | 写入并读取 `occupancy:test_status` | 数据一致 |

### 3.6 DB Consistency

| 用例编号 | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| DB-001 | `daily_stats` 表可访问性校验 | MySQL 正常 | 查询最新统计记录 | 返回 dict 或 None |
| DB-002 | `occupancy_events` 表可访问性校验 | MySQL 正常 | 查询最新事件记录 | 返回 dict 或 None |
| DB-003 | 状态接口与统计表基础一致性校验 | MySQL 正常 | 比较 `/api/status` 与 `daily_stats` | 非负字段与关键状态值一致 |
| DB-004 | 事件接口与事件表基础可读性校验 | MySQL 正常 | 请求 `/api/events`，查询最新事件 | 数据表可访问，事件结构合理 |
| DB-005 | 健康接口与数据库统计可共存校验 | MySQL 正常 | 请求 `/api/health`，查询数据库 | 服务状态与数据库访问均正常 |

## 4. 性能测试场景

### 4.1 status 轻量查询场景

- 目标接口：`/api/status`
- 目的：验证轻量读接口在常规并发范围内的稳定性
- 并发档位：20 / 50 / 100 / 200 / 300
- 判定指标：平均响应时间、P95、错误率

### 4.2 dashboard 混合查询场景

- 目标接口：`/api/status` + `/api/events` + `/api/history/events`
- 场景结构：`status 50% + events 30% + history 20%`
- 目的：模拟管理员工作台登录后的高频混合读取压力
- 并发档位：100 / 300 / 500 / 800
- 判定指标：平均响应时间、P95、错误率、资源峰值、熔断结果

### 4.3 实时链路烟测

- 目标接口：`WS /api/realtime`
- 目的：在 Jenkins 中验证登录后的实时链路至少可建连并收到首帧状态
- 校验方式：先登录获取 Cookie，再发起 WebSocket 连接
- 判定标准：成功收到 `type=status` 的消息

### 4.4 Redis 宕机与缓存雪崩区分说明

- 直接停止 Redis 更适合模拟“缓存不可用 / 节点宕机 / 缓存回源”
- 真正的缓存雪崩应结合“大量 key 同时过期 + 高并发请求 + 后端回源压力”共同模拟
- 因此测试设计上应至少拆成两类：
  - Redis 不可用容错测试
  - 大批量缓存失效下的高并发回源压力测试

## 4.5 当前已落地的代码级性能优化

- WebSocket 实时推送仅对管理员计算事件负载，普通用户只推状态，减少无效序列化与事件读取
- `daily_stats` 的 MySQL 同步增加节流窗口，避免高频循环下每次状态刷新都落库
- 错误请求方法测试改为参数化集中覆盖，降低测试重复代码并提高可维护性

## 5. 熔断规则

### JMeter 指标熔断

- 错误率 >= 1%
- P95 >= 1000ms

### 资源熔断（本轮放宽后）

- system_cpu >= 95%
- process_cpu >= 150%
- process_memory >= 2048MB
- process_threads >= 2000

## 6. 通过标准

- 功能自动化用例全部通过
- status 场景在既定测试范围内保持 0 错误率和稳定低延迟
- polling 场景能识别出性能退化过程和熔断拐点
- Jenkins 能自动执行并产出报告与结果归档
