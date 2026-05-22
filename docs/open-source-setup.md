# SCUM 开源版安装与构建说明

本文档补充根 README，聚焦本仓库对外公开后的安装、运行和构建约定。

## 后端环境变量

后端模板文件位于 `SCUM Robot/.env.example`，公开接口如下：

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `PAYMENT_CALLBACK_DOMAIN`
- `LOG_LEVEL`
- `DEBUG`
- `BOOTSTRAP_ADMIN_USERNAME`
- `BOOTSTRAP_ADMIN_PASSWORD`

首次初始化要求：

- `BOOTSTRAP_ADMIN_PASSWORD` 不能为空。
- 不能保留模板占位值。
- 若未配置，后端首次建库会阻塞失败。

## 前端环境变量

前端模板文件位于 `SCUM Robot Web/.env.example`：

```env
VITE_API_BASE_URL=http://localhost:8000
```

这是前端连接后端的唯一公开基地址入口。

## 开发模式

后端：

```powershell
uv run python "SCUM Robot\start_api.py"
```

前端：

```powershell
cd "SCUM Robot Web"
npm run dev
```

## 集成构建

前端构建命令：

```powershell
cd "SCUM Robot Web"
npm run build
```

构建结果会直接输出到后端 `SCUM Robot/public/`，保持当前集成模式不变。

保留目录：

- `SCUM Robot/public/images/items/imgs`
- `SCUM Robot/public/images/items/thumbs`
- `SCUM Robot/public/images/gifts/imgs`
- `SCUM Robot/public/images/gifts/thumbs`

这些目录用于运行时上传文件；源码仓库中只保留空占位文件。

## 发布前检查

首个公开提交前应确认：

- 未包含 `.env`
- 未包含任何 `*.db`
- 未包含 `backups/`
- 未包含 `node_modules/`
- 未包含 `.venv/`
- 未包含 `SCUM Robot/public/` 生成产物
- 未包含根目录或子目录中的 `zip/exe`

## 非目标范围

本次开源整理不包含：

- CI
- 自动发布
- Issue 模板
- 目录重构
- REST API 形状变更
