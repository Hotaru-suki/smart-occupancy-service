# API 说明

## 1. 接口分组

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

## 2. 认证说明

- 登录成功后，服务端写入 `HttpOnly Cookie`
- 受保护接口依赖该 Cookie
- `viewer` 仅有只读权限
- `admin` 可访问管理接口

详细规则见：[AUTH_RULES.md](./AUTH_RULES.md)

## 3. 关键接口

### `GET /`

返回服务基础信息。

示例响应：

```json
{
  "service": "Occupancy Detection Service",
  "version": "1.2.0",
  "mock": true,
  "supports_video": false,
  "ui": "/ui/"
}
```

### `POST /api/auth/login`

用户登录。

示例请求：

```json
{
  "username": "admin",
  "password": "ChangeMe123!"
}
```

示例响应：

```json
{
  "authenticated": true,
  "username": "admin",
  "role": "admin",
  "expires_at": 1719999999
}
```

### `POST /api/auth/register`

用户注册。管理员注册需要 `admin_registration_code`。

普通用户示例：

```json
{
  "username": "viewer_demo",
  "password": "ValidPass123!",
  "role": "viewer"
}
```

管理员示例：

```json
{
  "username": "ops_admin",
  "password": "ValidPass123!",
  "role": "admin",
  "admin_registration_code": "OccupancyAdmin2026!"
}
```

### `GET /api/status`

返回当前占用状态。

关键字段：

- `occupied`
- `status`
- `current_people`
- `occupied_duration_sec`
- `today_total_occupied_sec`
- `max_people_today`
- `roi`

### `GET /api/events`

管理员查看最近事件。

查询参数：

- `limit`: `1-100`

### `GET /api/history/events`

管理员查看历史事件。

查询参数：

- `region_name`
- `event_type`
- `limit`: `1-200`

### `PATCH /api/auth/password`

已登录用户修改自己的密码。

示例请求：

```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass123!"
}
```

### `GET /api/admin/users`

管理员查看用户列表。

### `PATCH /api/admin/users/{username}/role`

管理员修改用户角色。

示例请求：

```json
{
  "role": "admin"
}
```

### `DELETE /api/admin/users/{username}`

管理员删除单个用户。

限制：

- 不能删除自己
- 不能删除系统默认管理员

### `DELETE /api/admin/users`

管理员批量清理测试账号。

行为：

- 仅删除 `tester_` 前缀账号
- 不删除当前管理员
- 不删除系统默认管理员

### `POST /api/webrtc-offer`

建立 WebRTC 视频协商。

### `WS /api/realtime`

实时推送接口。

普通用户：

- 接收 `status`

管理员：

- 接收 `status`
- 接收 `events`

## 4. 常见错误码

- `200`：成功
- `201`：创建成功
- `400`：请求不合法，例如当前模式不支持视频
- `401`：未认证或密码错误
- `403`：权限不足或管理员注册码错误
- `404`：资源不存在
- `405`：错误请求方法
- `409`：冲突，例如重复注册、删除自己
- `422`：参数校验失败
- `429`：登录触发限流

## 5. 前端入口

- 页面入口：`/ui/`
- 登录后先走 HTTP 初始化，再通过 WebSocket 获取实时更新
