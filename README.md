# SCUM

> 当前仓库仍是持续整理中的半成品开源版本，但核心功能已经实现。
> 功能完整性、稳定性、文档覆盖、测试与易用性都还在持续完善中，请按“开发中项目”预期使用。

SCUM 是一个单仓库开源项目，包含：

- `SCUM Robot`：FastAPI 后端、数据库初始化、机器人能力、支付/备份管理
- `SCUM Robot Web`：Vue 3 + Vite 前端，开发时独立运行，生产构建输出到后端 `public/`

## 目录结构

```text
SCUM/
├─ SCUM Robot/        # Python 后端
├─ SCUM Robot Web/    # Vue 前端
├─ docs/              # 对外文档
├─ pyproject.toml
└─ build_deploy.py
```

## 环境要求

- Windows 10/11
- Python 3.13+
- Node.js 20+
- npm 10+

## 快速开始

### 1. 安装后端依赖

推荐使用 `uv`：

```powershell
uv sync
```

或使用 `pip`：

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r "SCUM Robot\requirements.txt"
```

### 2. 安装前端依赖

```powershell
cd "SCUM Robot Web"
npm install
cd ..
```

### 3. 复制并填写环境变量模板

后端：

```powershell
Copy-Item "SCUM Robot\.env.example" "SCUM Robot\.env"
```

前端：

```powershell
Copy-Item "SCUM Robot Web\.env.example" "SCUM Robot Web\.env"
```

至少需要配置：

- 后端：`DATABASE_URL`、`JWT_SECRET_KEY`、`PAYMENT_CALLBACK_DOMAIN`、`LOG_LEVEL`、`DEBUG`、`BOOTSTRAP_ADMIN_USERNAME`、`BOOTSTRAP_ADMIN_PASSWORD`
- 前端：`VITE_API_BASE_URL`

重要约束：

- 首次建库前必须显式设置 `BOOTSTRAP_ADMIN_PASSWORD`。
- 如果该值缺失或仍是占位值，后端首次初始化会直接失败并提示先配置。

开发默认值：

- `VITE_API_BASE_URL=http://localhost:8000`
- `PAYMENT_CALLBACK_DOMAIN=http://localhost:8000`

## 启动开发环境

### 后端

```powershell
uv run python "SCUM Robot\start_api.py"
```

启动后可访问：

- 健康检查：`http://localhost:8000/health`
- OpenAPI 文档：`http://localhost:8000/docs`

### 前端

```powershell
cd "SCUM Robot Web"
npm run dev
```

默认前端开发地址为 `http://localhost:3000`，通过 `VITE_API_BASE_URL` 连接后端。

## 生产构建与集成

前端生产构建会直接写入后端 `SCUM Robot/public/`：

```powershell
cd "SCUM Robot Web"
npm run build
```

构建后由后端统一提供 SPA 入口和静态资源，保留当前 `/static/` 集成机制。

更多说明见 [docs/open-source-setup.md](docs/open-source-setup.md)。

## 手工验收基线

在干净 Windows 环境中，应能按本文档完成：

1. 安装 Python 依赖。
2. 安装前端依赖。
3. 复制并填写两个 env 模板。
4. 启动后端。
5. 启动前端开发环境。
6. 首次启动自动建库并完成初始化。
7. 访问健康检查与 API 文档。
8. 前端开发环境成功连接后端。
9. 前端生产构建重新生成后端 `public` 内容。

## 权限说明

- `robot`、`backup`、支付配置和回调日志相关高风险接口要求管理员权限。
- 自定义窗口命令和窗口枚举接口要求超级管理员权限。
- 普通用户只能访问自己的订单与自身业务数据。

## 相关文档

- [docs/open-source-setup.md](docs/open-source-setup.md)
- [SCUM Robot Web/README.md](SCUM%20Robot%20Web/README.md)
