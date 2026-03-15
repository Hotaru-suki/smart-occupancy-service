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
| EVENTS-004 | limit=0 非法参数校验 | 服务已启动 | GET `/api/events?limit=0` | 返回 422 |
| EVENTS-005 | limit=101 非法参数校验 | 服务已启动 | GET `/api/events?limit=101` | 返回 422 |
| EVENTS-006 | limit=-1 非法参数校验 | 服务已启动 | GET `/api/events?limit=-1` | 返回 422 |
| EVENTS-007 | 非整型 limit 校验 | 服务已启动 | GET `/api/events?limit=abc` | 返回 422 |
| EVENTS-008 | 默认 limit 返回结构校验 | 服务已启动 | GET `/api/events` | 返回标准结构，事件数组元素结构正确 |

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

### 4.2 polling 混合轮询场景

- 目标接口：`/api/status` + `/api/events`
- 场景结构：`events 70% + status 30%`
- 目的：模拟更接近真实轮询的高频混合请求压力
- 并发档位：100 / 300 / 500 / 800
- 判定指标：平均响应时间、P95、错误率、资源峰值、熔断结果

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
