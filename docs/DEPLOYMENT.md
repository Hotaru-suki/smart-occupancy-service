# 部署与运行说明

## 目标读者

这份文档面向三类场景：

- 本地开发运行
- 本地测试与回归
- Jenkins 自动化集成

项目的配置策略是统一围绕 `.env` 工作，只是不同场景生成 `.env` 的来源不同。

## 环境文件策略

- `.env.example`：模板，占位配置，不写真实本地值
- `.env.dev`：本地开发使用的真实配置
- `.env.test`：本地测试使用的真实配置
- `.env.test.example`：Jenkins / SCM 模式使用的测试模板
- `.env`：应用运行时实际读取的配置文件

推荐约定：

- 开发时：复制 `.env.dev` 到 `.env`
- 测试时：复制 `.env.test` 到 `.env`
- Jenkins 中：流水线基于 `.env.test.example` 和 Jenkins 环境变量生成 `.env`

## 运行依赖

项目默认依赖：

- Python 虚拟环境
- Redis
- MySQL

本仓库通过 `docker-compose.yml` 提供 Redis 与 MySQL 的本地依赖服务。

启动方式：

```bash
docker compose up -d
```

停止方式：

```bash
docker compose down
```

## 本地开发

### 1. 准备环境文件

```powershell
Copy-Item .env.dev .env
```

### 2. 安装依赖

先在 Windows 中创建项目虚拟环境，统一使用 Windows Python 3.14 作为基座解释器：

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

```powershell
pip install -r requirements-dev.txt
```

如果只运行服务，不执行测试，也可以只安装：

```powershell
pip install -r requirements.txt
```

如果你在 PyCharm 里把项目解释器设成 `.venv\Scripts\python.exe`，Run/Debug 会直接使用这套环境，Terminal 也通常会自动激活。

### 3. 启动服务

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 4. 访问入口

- 前端：`http://127.0.0.1:8000/ui/`
- 根接口：`http://127.0.0.1:8000/`
- 健康检查：`http://127.0.0.1:8000/api/health`

## 本地测试

### 1. 切换到测试配置

```powershell
Copy-Item .env.test .env
```

### 2. 确保依赖服务已启动

```bash
docker compose up -d
```

### 3. 启动应用

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 4. 执行测试

```powershell
pytest tests
```

如果需要 Allure 结果：

```powershell
pytest tests --alluredir=allure-results
```

## Jenkins 集成

Jenkins 的配置链路是：

1. 检查仓库结构和依赖脚本
2. 基于 `.env.test.example` 和 Jenkins 环境变量生成 `.env`
3. 从 `.env` 读取运行配置
4. 启动 Docker 依赖服务
5. 安装依赖
6. 启动后端
7. 执行烟测、实时烟测、pytest、JMeter

Jenkins 当前需要提供这些关键值，用于生成 `.env`：

- `HOST`
- `PORT`
- `AUTH_USERNAME`
- `AUTH_PASSWORD`
- `ADMIN_REGISTRATION_CODE`
- `PYTHON_EXE`
- `JMETER_HOME`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DB`
- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_DB`

如果这些值没有通过 Jenkins 环境变量提供，就需要在 `.env.test.example` 中改成适合该 Jenkins 节点环境的非占位值。

## Docker 说明

当前 `docker-compose.yml` 负责启动：

- Redis
- MySQL

它的职责是提供开发与测试依赖，不负责直接启动 FastAPI 应用本身。应用仍然由本地命令或 Jenkins 脚本启动。

## 建议的日常操作

### 开发模式

```powershell
Copy-Item .env.dev .env
docker compose up -d
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 测试模式

```powershell
Copy-Item .env.test .env
docker compose up -d
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
pytest tests
```

## 常见注意事项

- 不要把真实本地值写进 `.env.example`
- `.env.dev` 和 `.env.test` 可以保留当前环境需要的真实配置
- Jenkins 不应依赖仓库内真实 `.env.test`，应通过环境变量生成 `.env`
- 如果 Jenkins 跑不起来，先检查必填环境变量是否仍是占位值
- 如果本地依赖升级后出现兼容问题，优先检查 Python 客户端依赖版本，而不是先怀疑 Redis/MySQL 服务端
