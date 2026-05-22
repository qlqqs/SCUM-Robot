# SCUM Robot Web

本目录是 SCUM 项目的前端子项目，使用 Vue 3 + Vite。

根级 [README.md](../README.md) 是整个仓库的唯一权威入口；本文档只说明前端职责、环境变量和常用命令。

## 前端职责

- 提供用户侧商城、礼包、充值、个人资料页面
- 提供管理员后台页面
- 开发时通过 `VITE_API_BASE_URL` 访问后端 API
- 生产构建时将静态资源输出到 `../SCUM Robot/public/`

## 环境变量

复制模板：

```powershell
Copy-Item ".env.example" ".env"
```

模板内容：

```env
VITE_API_BASE_URL=http://localhost:8000
```

源码中允许出现的本地默认值仅用于文档化开发环境：`http://localhost:8000`

## 常用命令

安装依赖：

```powershell
npm install
```

启动开发服务器：

```powershell
npm run dev
```

生产构建到后端 `public/`：

```powershell
npm run build
```

清理后端已生成的前端产物：

```powershell
npm run clean
```

格式化与 lint：

```powershell
npm run lint
npm run format
```
