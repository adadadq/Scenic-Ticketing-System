# 模拟支付回调安全边界设计

## 1. 问题定义

当前支付接口是游客浏览器主动调用 `POST /api/orders/{order_no}/pay`：它依赖游客 session、session-bound CSRF 和 `Idempotency-Key`。真实支付平台回调不是浏览器请求，不能依赖游客 Cookie 或 CSRF；它必须依赖服务端共享密钥验签、时间戳防重放和事件幂等。

本切片实现一个模拟第三方支付成功回调，用来学习真实回调安全边界，但不接入微信、支付宝或银行渠道。

## 2. 范围

包含：

- `POST /api/payments/mock/callback`。
- 请求头 `X-Mockpay-Timestamp` 和 `X-Mockpay-Signature`。
- HMAC-SHA256 验签，签名文本为 `timestamp + "." + raw_body`。
- 路由先读取原始 body 并完成验签，再解析请求体字段。
- 时间戳防重放，默认允许 300 秒偏差。
- `eventId` 全局幂等，重复成功回调不重复扣库存、不重复出票。
- 只处理支付成功事件。
- 回调成功后复用现有支付状态机：扣 `quota_sold`、写 `payment_record`、出票、订单变为已支付。

不包含：

- 真实微信/支付宝 SDK。
- 支付失败通知。
- 退款通知。
- 对账文件。
- 回调 IP 白名单。
- 前端页面实现。

## 3. API 契约

```http
POST /api/payments/mock/callback
X-Mockpay-Timestamp: 1782892800
X-Mockpay-Signature: <hex hmac-sha256>
Content-Type: application/json
```

请求体：

```json
{
  "eventId": "evt_202607010001",
  "orderNo": "O202607010900000001",
  "paymentNo": "P202607010001",
  "transactionNo": "T202607010001",
  "paidAmount": "256.00",
  "paymentStatus": "SUCCESS"
}
```

成功响应 `MockPaymentCallbackDTO`：

```json
{
  "eventId": "evt_202607010001",
  "orderNo": "O202607010900000001",
  "orderStatus": "PAID",
  "paymentStatus": "PAID",
  "idempotent": false,
  "processedAt": "2026-07-01T09:00:00Z"
}
```

错误：

- 缺少或非法签名头：`401 MOCKPAY_SIGNATURE_INVALID`。
- 时间戳超出允许窗口：`401 MOCKPAY_TIMESTAMP_INVALID`。
- 请求体不是成功支付事件：`422 MOCKPAY_EVENT_INVALID`。
- 订单不存在：`404 MOCKPAY_ORDER_NOT_FOUND`。
- 金额不匹配：`409 MOCKPAY_AMOUNT_MISMATCH`。
- 订单状态不可支付或库存不足：复用 `ORDER_NOT_PAYABLE` / `TIME_SLOT_QUOTA_NOT_ENOUGH`。

## 4. 权限与安全

- 回调接口不接受游客 session，也不要求 CSRF。
- 只信任 HMAC 签名和时间戳。
- 签名密钥来自 `MOCKPAY_CALLBACK_SECRET`，生产环境禁止使用默认开发密钥。
- 生产环境同时拒绝 `.env.example` 的占位回调密钥。
- 使用 `hmac.compare_digest` 比较签名。
- 签名验证失败时不进入数据库状态机。
- 错误响应不返回签名密钥、原始签名、完整请求体、SQL、订单内部 id 或堆栈。

## 5. 数据与幂等

- `eventId` 映射到 `payment_record.idempotency_key = "mockpay:" + eventId`，并通过部分唯一索引保证 `mockpay:%` 事件全局唯一。
- repository 在事务内锁定订单和订单明细。
- 已处理过的 `eventId` 返回幂等成功，不重复扣库存或出票。
- 新 `eventId` 命中已支付订单时不能伪装成幂等成功，仍需按金额和状态机拒绝。
- 支付金额必须等于订单 `payable_amount`。
- 订单必须是 `CREATED + UNPAID`，明细必须是 `PENDING_PAYMENT`。
- 库存扣减继续使用条件更新，避免超卖。

## 6. 验收

目标测试：

```bash
.venv/bin/pytest backend/tests/test_mock_payment_callback_api.py backend/tests/test_openapi_contract.py backend/tests/test_config_db.py -q
```

覆盖：

- 合法签名回调支付成功。
- 缺签名、签名错误、过期时间戳不能进入 repository。
- 重复 `eventId` 不重复扣库存或出票。
- 金额不匹配、订单不存在、订单状态不合法返回领域错误。
- GET/游客 CSRF 机制不参与回调。
- OpenAPI 暴露回调 DTO 和签名头。
- 生产环境拒绝默认回调密钥。
