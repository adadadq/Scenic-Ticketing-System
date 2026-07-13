# 遇龙河票务前端

React + TypeScript + Vite + Ant Design 前端，包含游客移动端和景区运营管理端。

## 页面

- `/#/visitor/booking`：票种、日期时段、常用出行人、订单确认和支付。
- `/#/visitor/orders`：订单筛选、详情、票码、继续支付、取消和退款。
- `/#/visitor/service`：开放时间、入园说明、交通路线和退改说明。
- `/#/admin`：票种、系统设置、订单、核销、退款审计、报表和导出任务。

## 常用命令

```bash
npm ci
npm run dev
npm run lint
npm run test:contract
npm run test:e2e
npm run test:e2e:real
npm run build
```

`test:e2e` 使用临时 mock API 验证当前游客端注册登录、常用出行人、下单、支付、退款和移动端布局；管理端接口与权限回归由后端 pytest 契约测试覆盖。

开发服务器默认把 `/api` 代理到 `http://127.0.0.1:8000`。如需连接其他后端：

```bash
E2E_API_BASE_URL=http://127.0.0.1:8001 npm run test:e2e:real
```

如果 Chrome 不在默认 macOS 路径，设置 `CHROME_PATH=/path/to/chrome`。

## 目录

```text
src/
  app/                     游客端和管理端应用壳
  features/auth/           游客注册、登录和会话
  features/booking/        购票、时段、出行人与支付流程
  features/orders/         游客订单、票码、取消与退款
  features/visitor-service/ 游客服务页面
  features/admin/          管理端工作台
  features/admin-*/        管理端认证、订单、报表与审计请求
  shared/api/              API client、DTO 和 endpoint
  shared/theme/            Ant Design 主题 token
```

## 接口约定

- API 事实源：`../docs/api-contract.md`。
- 状态变更请求自动携带 CSRF header。
- 支付请求必须携带 `Idempotency-Key`。
- 游客身份、订单归属和管理员权限均以后端 session 为准。
- 前端与 API 使用 Cookie 时必须保持 hostname 一致。

## 移动端验收

关键页面以 iPhone 15 Pro 的 `393 × 852` 视口为主验收规格，同时要求页面无横向滚动、固定操作栏不遮挡内容、导航与登录/退出按钮不重叠。
