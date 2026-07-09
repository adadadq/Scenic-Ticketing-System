# 旧版 Node 基线

本目录保存重构前的 Express + 静态页面版本，只作为接口、业务规则和测试用例的参考源。

当前主线是根目录下的 FastAPI 后端、`frontend/` React 前端和 `database/` SQL 结构。新增功能、修复和联调验收应优先修改当前主线，不在这里继续扩展旧版实现。

## 内容

- `package.json` / `package-lock.json`：旧版 Node 依赖和脚本。
- `src/`：旧版 Express 后端源码。
- `public/`：旧版静态页面。
- `tests/`：旧版 Node 测试。

## 安全边界

- 不归档真实 `.env`、数据库密码、Cookie、CSRF token 或线上密钥。
- 如果从旧版复制业务规则到当前后端，必须重新经过 DTO、防越权、CSRF、错误脱敏和 pytest 验收。
