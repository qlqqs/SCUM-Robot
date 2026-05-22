# Third-Party Notices

本项目基于若干第三方开源组件构建，核心依赖及其许可证类型如下：

- Python：FastAPI, Uvicorn, SQLAlchemy, PyJWT, Passlib, bcrypt, Pillow, pycryptodome, cryptography, python-dotenv, pytest, PyInstaller
- 前端：Vue, Vue Router, Pinia, Vite, Axios, Tailwind CSS, Font Awesome Free, `@fontsource/inter`

这些依赖大多采用 MIT、BSD、Apache-2.0 或同类宽松许可证。更完整的版本与传递依赖信息可参考：

- 后端依赖定义：`pyproject.toml`、`SCUM Robot/requirements.txt`
- 前端依赖定义：`SCUM Robot Web/package.json`

发布前如需生成更正式的第三方许可证清单，建议分别执行：

- Python：基于锁文件或虚拟环境导出许可证报告
- 前端：基于 `package-lock.json` 生成 npm 许可证报告
