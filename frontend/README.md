# 遇龙河票务前端

React + TypeScript + Vite + Ant Design 前端工程。当前阶段先完成游客购票工作台、我的订单、接口契约层和响应式基础体验。

## 常用命令

```bash
npm install
npm run dev
npm run build
npm run lint
npm run test:e2e
npm run test:e2e:real
```

开发服务器默认通过 Vite 代理把 `/api` 转发到 `http://127.0.0.1:8000`，如需直连其他后端地址可设置 `VITE_API_BASE_URL`。
`npm run test:e2e` 默认会启动临时 mock API、临时 Vite 服务和本机 Chrome，验证游客登录、实名、下单、支付、票码展示和 390px 移动端无横向溢出。
后端线程启动真实 API 后，可用 `npm run test:e2e:real` 让 E2E 通过 Vite `/api` 代理直连 `http://127.0.0.1:8000`，避免浏览器页面和 API 混用不同 hostname；脚本会先检查 `/api/health` 和 `/api/health/db`。
如需连接其他后端地址，可用 `E2E_API_BASE_URL=http://127.0.0.1:8001 npm run test:e2e` 覆盖。
根目录联调门禁也支持真实浏览器 smoke：`VERIFY_INTEGRATION_E2E=real scripts/verify-integration.sh`，同样可通过 `E2E_API_BASE_URL` 覆盖真实后端地址；前端日常开发仍默认使用 `npm run test:e2e` 的 mock API，根目录 `mock` 模式会忽略外部 `E2E_API_BASE_URL`。
如果 Chrome 不在默认 macOS 路径，可设置 `CHROME_PATH=/path/to/chrome` 后再运行；真实后端模式还可设置 `E2E_VISITOR_NAME`、`E2E_PHONE`、`E2E_ID_NUMBER` 避免测试实名信息冲突。

## 契约约定

- API source of truth: `../docs/api-contract.md`
- 状态变更请求自动携带 CSRF header。
- `POST /api/orders/{order_no}/pay` 必须传 `Idempotency-Key`。
- 游客身份从后端 session 读取，前端不提交资源归属字段。

## 当前目录

```text
src/
  features/auth/    游客会话查询、手机号登录、实名登记和退出入口
  features/booking/ 游客购票工作台页面、静态演示数据和页面私有类型
  features/orders/  我的订单页面、订单查询/支付 query 和 view model adapter
  shared/api/      API client、DTO 类型、endpoint wrapper
  shared/theme/    Ant Design 主题 token
  App.tsx          应用壳、导航和全局主题入口
```
