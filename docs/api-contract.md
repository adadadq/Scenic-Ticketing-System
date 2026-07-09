# API 契约

## 公共接口

```text
GET  /api/health
GET  /api/health/db
GET  /api/catalog/products
GET  /api/catalog/time-slots
GET  /api/announcements/current
POST /api/auth/visitor/login
POST /api/auth/visitor/register
GET  /api/auth/csrf
POST /api/auth/logout
```

## 游客接口

```text
GET  /api/auth/me
GET  /api/me/passenger-templates
POST /api/me/passenger-templates
PATCH /api/me/passenger-templates/{template_id}
DELETE /api/me/passenger-templates/{template_id}
POST /api/orders
POST /api/orders/{order_no}/pay
POST /api/orders/{order_no}/cancel
GET  /api/me/orders
GET  /api/me/orders/{order_no}
```

## 管理员接口

```text
POST /api/admin/auth/login
GET  /api/admin/auth/me
PATCH /api/admin/auth/profile
POST /api/admin/auth/logout
POST /api/admin/announcements/current
POST /api/admin/export-jobs
GET  /api/admin/export-jobs
GET  /api/admin/export-job-alert-events
GET  /api/admin/export-job-alert-events/summary
POST /api/admin/export-job-alert-events/{event_id}/acknowledge
POST /api/admin/export-job-alert-events/batch-acknowledge
POST /api/admin/export-job-alert-events/batch-delete
POST /api/admin/export-job-alert-events/{event_id}/close
POST /api/admin/export-job-alert-events/batch-close
POST /api/admin/export-job-alert-events/{event_id}/reopen
DELETE /api/admin/export-job-alert-events/{event_id}
GET  /api/admin/export-jobs/{job_id}
POST /api/admin/export-jobs/{job_id}/retry
GET  /api/admin/export-jobs/{job_id}/download
GET  /api/admin/orders
GET  /api/admin/orders/{order_no}
GET  /api/admin/orders/{order_no}/refund-logs
GET  /api/admin/refund-logs
GET  /api/admin/refund-logs.csv
GET  /api/admin/refund-logs.xlsx
POST /api/admin/check-ins
POST /api/admin/check-ins/batch
POST /api/admin/check-ins/batch/undo
POST /api/admin/check-ins/{ticket_code}/undo
GET  /api/admin/check-ins/{ticket_code}/logs
GET  /api/admin/check-in-failure-logs
GET  /api/admin/check-in-failure-logs.csv
GET  /api/admin/check-in-failure-logs.xlsx
GET  /api/admin/check-in-logs
GET  /api/admin/check-in-logs.csv
GET  /api/admin/check-in-logs.xlsx
POST /api/admin/orders/{order_no}/refund
POST /api/admin/orders/{order_no}/refund/items
GET  /api/admin/reports/summary
GET  /api/admin/reports/payment-reconciliation
GET  /api/admin/reports/payment-reconciliation.csv
GET  /api/admin/reports/payment-reconciliation.xlsx
GET  /api/admin/reports/product-breakdown
GET  /api/admin/reports/product-breakdown.csv
GET  /api/admin/reports/product-breakdown.xlsx
GET  /api/admin/reports/daily-trend
GET  /api/admin/reports/daily-trend.csv
GET  /api/admin/reports/daily-trend.xlsx
GET  /api/admin/reports/hourly-trend
GET  /api/admin/reports/hourly-trend.csv
GET  /api/admin/reports/hourly-trend.xlsx
GET  /api/admin/reports/monthly-trend
GET  /api/admin/reports/monthly-trend.csv
GET  /api/admin/reports/monthly-trend.xlsx
GET  /api/admin/reports/orders.csv
GET  /api/admin/reports/orders.xlsx
GET  /api/admin/settings
PATCH /api/admin/settings
GET  /api/admin/tickets
POST /api/admin/tickets
PATCH /api/admin/tickets/{ticket_id}
DELETE /api/admin/tickets/{ticket_id}
POST /api/payments/mock/callback
```

## 状态变更要求

- 状态变更接口必须校验 CSRF。
- 已登录后的状态变更接口必须校验 CSRF token 与当前 session 保存的 `csrf_token_hash` 匹配，不能只依赖 header/cookie 相等。
- 支付接口必须带 `Idempotency-Key`。
- 当前支付 provider 只支持 `PAYMENT_PROVIDER=mock`；未实现的 `wechat`、`alipay`、`stripe`、`unionpay` 或其他真实支付 provider 会在配置校验阶段拒绝启动，不能静默回退到模拟支付。
- 当前短信 provider 只支持 `SMS_PROVIDER=disabled`；未实现的 `aliyun`、`tencent`、`twilio` 或其他真实短信 provider 会在配置校验阶段拒绝启动，不能静默回退到手机号直登演示流。
- 游客接口从会话中读取 `visitor_id`，不信任前端提交的归属字段。
- `GET /api/auth/csrf` 设置可读 CSRF Cookie，响应 `data.headerName`，不在 JSON 中返回 token；如果请求已带有效 session，后端会把新 CSRF hash 绑定到当前 session。
- CSRF Cookie 由前端通过 `document.cookie` 读取，因此本地联调时前端页面和 API URL 必须使用相同 hostname；允许端口不同，但不要混用 `localhost` 与 `127.0.0.1`。

## 公告接口约定

- `GET /api/announcements/current` 公开返回当前游客公告，供购票页和游客服务页展示；这是只读 GET，不要求登录或 CSRF header。
- `POST /api/admin/announcements/current` 只接受管理员 session，并且必须携带 CSRF header；请求体只允许 `title` 和 `content`，成功后替换当前公告。
- 公告 DTO 只返回 `title`、`content`、`updatedAt`、`operatorDisplayName`，不返回 session、CSRF token、内部管理员 id 或操作日志明细。

## 后台同步导出上限约定

- 多行后台同步导出包含订单明细、核销审计、核销失败审计、退款审计、产品维度报表和趋势报表的 CSV/XLSX 文件响应。
- 同步导出最多返回 `SYNC_EXPORT_ROW_LIMIT` 行数据；后端查询使用 `SYNC_EXPORT_ROW_LIMIT + 1` 作为探测上限。
- 超过同步导出上限返回 `413 ADMIN_EXPORT_TOO_LARGE`，响应仍是统一失败壳；前端应提示用户缩小日期或筛选范围，后续异步导出切片再提供大文件任务流。
- 支付对账汇总导出是固定单行汇总，不适用行数上限。

## 后台异步导出任务约定

- `POST /api/admin/export-jobs` 只接受管理员 session，并且必须携带 CSRF header。
- 请求体使用 `exportType`、`fileFormat`、`filters`；`exportType` 当前允许 `ORDER_DETAIL`、`CHECK_IN_AUDIT`、`CHECK_IN_FAILURE_AUDIT`、`REFUND_AUDIT`、`PAYMENT_RECONCILIATION`、`PRODUCT_BREAKDOWN`、`DAILY_TREND`、`HOURLY_TREND`、`MONTHLY_TREND`，`fileFormat` 当前允许 `CSV`、`XLSX`。
- 请求体拒绝额外字段；前端不能提交 `adminUserId`、数据库内部 id、任务状态、文件路径或下载链接。
- `filters` 必须是 JSON object，后端限制序列化后大小，并按 `exportType` 校验字段白名单，避免把大对象或客户端控制字段写入任务表。
- `ORDER_DETAIL`、`PAYMENT_RECONCILIATION`、`PRODUCT_BREAKDOWN` 只允许 `dateFrom`、`dateTo`。
- `DAILY_TREND`、`HOURLY_TREND`、`MONTHLY_TREND` 只允许 `dateFrom`、`dateTo`、`includeEmpty`。
- `CHECK_IN_AUDIT` 只允许 `ticketCode`、`orderNo`、`operatorUsername`、`reason`、`dateFrom`、`dateTo`。
- `CHECK_IN_FAILURE_AUDIT` 只允许 `ticketCode`、`failureCode`、`operatorUsername`、`dateFrom`、`dateTo`。
- `REFUND_AUDIT` 只允许 `refundType`、`orderNo`、`operatorUsername`、`dateFrom`、`dateTo`。
- `filters` 字段会被归一化：短文本 trim，空文本丢弃，日期必须是 `YYYY-MM-DD` 且起止顺序合法，`failureCode` 和 `refundType` 归一化为大写，`includeEmpty` 归一化为布尔值；非法 filters 返回 `422 ADMIN_EXPORT_JOB_FILTERS_INVALID`。
- 创建成功返回 `AdminExportJobDTO`，状态为 `PENDING`；当前创建接口只登记任务，不同步生成文件。
- `AdminExportJobDTO.filters` 是公开响应字段：`ticketCode`、`orderNo`、`operatorUsername`、`reason` 的值会返回 `***`，日期、枚举和布尔筛选保持原值；worker 内部仍使用数据库中完整 `filters` 生成文件。
- `AdminExportJobDTO.requestId` 保存创建导出任务时的请求 id，可用于前端任务状态、后端请求日志和 worker 输出之间的排障关联；历史任务可能为 `null`。
- 内部 worker 状态机按 `PENDING -> RUNNING -> SUCCEEDED/FAILED` 流转；worker 领取任务时使用行锁避免重复领取，成功时可写入文件名和内部 `storage_key`，失败时写入错误码和错误信息；超过 30 分钟仍处于 `RUNNING` 的任务会在下一轮 worker 领取前按自动重试额度回收，耗尽后落为 `FAILED + ADMIN_EXPORT_JOB_WORKER_TIMEOUT`。
- worker 写出本地文件后，如果成功落库返回 `None` 或抛出异常，会尽力删除刚生成的本地文件并保留原失败语义，避免未被任务元数据引用的孤儿文件积累。
- worker 未预期异常会使用内部 `retry_count/max_retries` 自动重试一次：第一次 `ADMIN_EXPORT_JOB_WORKER_FAILED` 会回到 `PENDING`，并通过内部 `next_attempt_at` 延迟 60 秒后才允许再次领取，耗尽后才落为 `FAILED`；业务/校验失败、未知导出类型或格式、手动中断不自动重试。
- worker 通过 `mark_export_job_failed` 标记为最终 `FAILED`，或 RUNNING 超时回收耗尽重试额度落为 `FAILED + ADMIN_EXPORT_JOB_WORKER_TIMEOUT` 时，会写入内部 `admin_export_job_alert_event` 作为本地告警事实；同一个 `jobId + errorCode + alertSource` 的未关闭事件重复出现时会折叠到原事件，更新 `occurrenceCount` 和 `lastSeenAt`；事件不进入导出任务 DTO，不包含 `filters`、`storage_key`、异常堆栈、本机路径或 SQL。当前提供管理员只读查询 API、汇总 API 和内部确认 API，不发送真实外部通知。
- worker 失败字段长度契约为 `errorCode` 最长 80、`errorMessage` 最长 500；服务层校验、`admin_export_job` 表和内部告警事件表保持一致，避免校验通过后数据库写入失败。
- 当前内部 worker 支持 `ORDER_DETAIL + CSV/XLSX`、`CHECK_IN_AUDIT + CSV/XLSX`、`CHECK_IN_FAILURE_AUDIT + CSV/XLSX`、`REFUND_AUDIT + CSV/XLSX`、`PAYMENT_RECONCILIATION + CSV/XLSX`、`PRODUCT_BREAKDOWN + CSV/XLSX`、`DAILY_TREND + CSV/XLSX`、`HOURLY_TREND + CSV/XLSX` 和 `MONTHLY_TREND + CSV/XLSX`，会复用后台订单 CSV/XLSX、核销审计 CSV/XLSX、核销失败审计 CSV/XLSX、退款审计 CSV/XLSX、支付对账 CSV/XLSX、产品维度报表 CSV/XLSX、日报趋势 CSV/XLSX、小时趋势 CSV/XLSX 与月度趋势 CSV/XLSX 导出口径生成文件；异常任务元数据中的未知导出类型或格式暂时标记为 `FAILED`，错误码为 `ADMIN_EXPORT_JOB_UNSUPPORTED`。
- 本地或部署环境可通过 `scripts/process-admin-export-job.py` 单次处理一条 pending 任务；脚本输出 JSON，包含 `processed` 和公开任务 DTO，任务 DTO 中的 `filters` 与公开 API 一样会脱敏敏感筛选值。
- 本地或部署环境可通过 `scripts/run-admin-export-worker.py --max-idle-loops 12 --idle-sleep-seconds 5` 循环处理 pending 任务；脚本输出单个 JSON 汇总，包含 `processed`、`idleLoops`、脱敏后的 `lastJob` 和固定错误对象，参数错误或启动异常不会输出本机路径或异常文本。
- Linux 部署环境可参考 `deploy/systemd/scenic-ticket-admin-export-worker.service` 让循环 worker 常驻运行；模板约定非 root 用户、`/etc/scenic-ticket/backend.env` 环境文件、`/var/lib/scenic-ticket/admin-exports` 受控导出目录、自动重启和 `SIGINT` 停止信号。
- Linux 部署环境可参考 `deploy/systemd/scenic-ticket-admin-export-cleanup.service` 和 `deploy/systemd/scenic-ticket-admin-export-cleanup.timer` 每日调度过期导出文件清理；模板使用 oneshot、非 root 用户、同一环境文件、受控导出目录、随机延迟和错过补跑。
- 当前导出文件存储 provider 只支持 `ADMIN_EXPORT_STORAGE_PROVIDER=local`；未实现的 `s3`、`oss` 或其他 provider 会在配置校验阶段拒绝启动，API、单次 worker、循环 worker 和清理脚本统一通过 storage factory 获取本地存储实现。
- 当前异步导出队列 provider 只支持 `ADMIN_EXPORT_QUEUE_PROVIDER=database`；未实现的 `redis`、`celery`、`rq` 或其他 provider 会在配置校验阶段拒绝启动，任务领取仍使用数据库行锁和状态条件。
- 当前异步导出失败告警 provider 只支持 `ADMIN_EXPORT_ALERT_PROVIDER=disabled`；未实现的 `email`、`slack`、`webhook` 或其他 provider 会在配置校验阶段拒绝启动，避免部署误以为失败告警已接入。
- 本地或部署环境可通过 `scripts/cleanup-admin-export-files.py --older-than-days 7 --limit 100` 清理过期成功任务文件，也可通过 `systemctl enable --now scenic-ticket-admin-export-cleanup.timer` 启用每日清理；清理只处理 `SUCCEEDED` 且已有内部 `storage_key` 的任务，删除文件后清空文件名和内部 `storage_key`，缺失文件也会清空过期元数据，异常路径会跳过且不会越出 `ADMIN_EXPORT_STORAGE_DIR`。
- `POST /api/admin/export-jobs/{job_id}/retry` 只接受管理员 session，并且必须携带 CSRF header；只允许把 `FAILED` 任务重置为 `PENDING`，同时清空 `startedAt`、`finishedAt`、`fileName`、`errorCode`、`errorMessage`、内部 `storage_key`、自动重试计数和 `next_attempt_at`，其他状态返回 `409 ADMIN_EXPORT_JOB_RETRY_NOT_ALLOWED`。
- `GET /api/admin/export-jobs`、`GET /api/admin/export-jobs/{job_id}` 和 `GET /api/admin/export-jobs/{job_id}/download` 只接受管理员 session；这是只读 GET，不要求 CSRF header。
- 列表支持 `exportType`、`fileFormat`、`status`、`page`、`pageSize` 查询参数；`fileFormat` 当前允许 `CSV`、`XLSX`，`status` 当前允许 `PENDING`、`RUNNING`、`SUCCEEDED`、`FAILED`。
- `GET /api/admin/export-job-alert-events` 只接受管理员 session；这是只读 GET，不要求 CSRF header。列表支持 `jobId`、`exportType`、`fileFormat`、`errorCode`、`acknowledged`、`closed`、`dateFrom`、`dateTo`、`page`、`pageSize` 查询参数，`exportType`、`fileFormat` 和 `errorCode` 会归一化为大写，`acknowledged` 和 `closed` 只接受 `true/false`，日期必须是 `YYYY-MM-DD` 且起止不能倒挂，筛选条件不合法返回 `422 ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID`。
- `GET /api/admin/export-job-alert-events/summary` 只接受管理员 session；这是只读 GET，不要求 CSRF header。汇总支持 `exportType`、`fileFormat`、`closed`、`dateFrom`、`dateTo` 查询参数，`exportType` 和 `fileFormat` 会归一化为大写，`closed` 只接受 `true/false`，日期按 `created_at` 过滤且 `dateTo` 包含当天；日期必须是 `YYYY-MM-DD` 且起止不能倒挂，筛选条件不合法返回 `422 ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID`。响应为 `AdminExportJobAlertEventSummaryDTO`，只包含 `total`、`acknowledged`、`unacknowledged`、`closed`、`open` 和按错误码聚合的 `byErrorCode`；每个 `byErrorCode` 分组同样返回 `closed` 和 `open`。
- `POST /api/admin/export-job-alert-events/{event_id}/acknowledge` 只接受管理员 session，并且必须携带 CSRF header；请求体只允许可选 `note`，最大 200 字符，空白归一化为 `null`。确认采用第一次确认获胜，重复确认返回既有确认记录，不覆盖原确认人或备注；事件不存在返回 `404 ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND`，备注非法返回 `422 ADMIN_EXPORT_JOB_ALERT_EVENT_ACK_INVALID`。
- `POST /api/admin/export-job-alert-events/batch-acknowledge` 只接受管理员 session，并且必须携带 CSRF header；请求体为 `{ "eventIds": [1, 2], "note": "已处理" }`，`eventIds` 至少 1 项、最多 100 项，事件 id 必须为正整数，不允许重复、snake_case 字段或额外字段；`note` 可选，最大 200 字符，空白归一化为 `null`。接口逐项复用确认逻辑，已确认事件返回成功但不覆盖第一次确认记录，不存在事件作为逐项失败返回；成功响应为 `AdminExportJobAlertEventBatchAcknowledgeDTO`，包含 `totalCount`、`successCount`、`failureCount` 和逐项 `results`，逐项结果只返回 `eventId`、`acknowledged`、可选 `code/message`。
- `POST /api/admin/export-job-alert-events/batch-delete` 只接受管理员 session，并且必须携带 CSRF header；请求体为 `{ "eventIds": [1, 2] }`，至少 1 项、最多 100 项，事件 id 必须为正整数，不允许重复或额外字段。接口只删除已关闭事件，未关闭事件和不存在事件作为逐项业务失败返回，不影响同批其他事件；成功响应为 `AdminExportJobAlertEventBatchDeleteDTO`，包含 `totalCount`、`successCount`、`failureCount` 和逐项 `results`，逐项结果只返回 `eventId`、`deleted`、可选 `code/message`。
- `POST /api/admin/export-job-alert-events/{event_id}/close` 只接受管理员 session，并且必须携带 CSRF header；请求体只允许可选 `note`，最大 200 字符，空白归一化为 `null`。关闭采用第一次关闭获胜，重复关闭返回既有关闭记录，不覆盖原关闭人或备注；事件不存在返回 `404 ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND`，备注非法返回 `422 ADMIN_EXPORT_JOB_ALERT_EVENT_CLOSE_INVALID`。
- `POST /api/admin/export-job-alert-events/batch-close` 只接受管理员 session，并且必须携带 CSRF header；请求体为 `{ "eventIds": [1, 2], "note": "已处理" }`，`eventIds` 至少 1 项、最多 100 项，事件 id 必须为正整数，不允许重复、snake_case 字段或额外字段；`note` 可选，最大 200 字符，空白归一化为 `null`。接口逐项复用关闭逻辑，已关闭事件返回成功但不覆盖第一次关闭记录，不存在事件作为逐项失败返回；成功响应为 `AdminExportJobAlertEventBatchCloseDTO`，包含 `totalCount`、`successCount`、`failureCount` 和逐项 `results`，逐项结果只返回 `eventId`、`closed`、可选 `code/message`。
- `POST /api/admin/export-job-alert-events/{event_id}/reopen` 只接受管理员 session，并且必须携带 CSRF header；重开会清空关闭展示字段，未关闭事件重复重开返回当前事件，事件不存在返回 `404 ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND`。
- `DELETE /api/admin/export-job-alert-events/{event_id}` 只接受管理员 session，并且必须携带 CSRF header；只允许删除已关闭事件，成功返回 `AdminExportJobAlertEventDeleteDTO`，其中只包含 `eventId` 和 `deleted=true`。未关闭事件返回 `409 ADMIN_EXPORT_JOB_ALERT_EVENT_DELETE_NOT_ALLOWED`，事件不存在返回 `404 ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND`。
- `AdminExportJobAlertEventDTO` 只返回 `eventId`、`jobId`、`exportType`、`fileFormat`、`errorCode`、`errorMessage`、`alertSource`、`createdAt`、`occurrenceCount`、`lastSeenAt`、`acknowledgedAt`、`acknowledgedByUsername`、`acknowledgedByDisplayName`、`acknowledgeNote`、`closedAt`、`closedByUsername`、`closedByDisplayName`、`closeNote`，不返回 `filters`、`storageKey`、`storage_key`、本机路径、SQL、堆栈、原始异常、session、CSRF token 或内部管理员 id。
- 任务不存在返回 `404 ADMIN_EXPORT_JOB_NOT_FOUND`。
- `GET /api/admin/export-jobs/{job_id}/download` 只允许下载 `SUCCEEDED` 且已经写入 `file_name`、`storage_key` 的任务；未生成或元数据不完整返回 `409 ADMIN_EXPORT_JOB_FILE_NOT_READY`。
- 下载成功响应是文件，不是统一 JSON 成功壳；CSV 使用 `text/csv; charset=utf-8`，XLSX 使用 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，并带 `Content-Disposition` 下载文件名。
- 若任务元数据存在但服务端文件缺失，返回 `404 ADMIN_EXPORT_FILE_NOT_FOUND`；后端会把内部 `storage_key` 限制在 `ADMIN_EXPORT_STORAGE_DIR` 内，拒绝路径穿越。
- 响应 DTO 不返回存储路径、内部 `storage_key`、完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id 或 `adminUserId`；只返回公开 `jobId`。

## Health DTO 约定

- `GET /api/health` 只检查 API 进程可用性，成功返回 `status`、`service`、`environment`。
- `GET /api/health/db` 检查数据库连接和 `SELECT 1 AS ok`，成功返回 `status`、`database`、`service`、`environment`。
- 数据库健康检查失败返回 `503 DATABASE_UNAVAILABLE`，不返回 DSN、密码、host 或底层异常细节。

## Auth DTO 约定

- Auth visitor DTO 对外使用 camelCase 字段。
- `POST /api/auth/visitor/login` 请求体为 `{ "phone": "13911112222" }`，成功返回 `VisitorMeDTO`。
- `POST /api/auth/visitor/register` 请求体使用 `visitorName`、`idType`、`idNumber`、`phone`，当前 `idType` 只支持 `ID_CARD`。
- Auth 请求体拒绝额外字段；前端不能提交 `visitorId`、`sessionToken`、`csrfToken` 等客户端控制字段。
- `GET /api/auth/me` 已登录时返回 `VisitorMeDTO`；未登录返回 `401 AUTH_REQUIRED`，不返回 `{ "user": null }`。
- `VisitorMeDTO` 至少包含 `visitorId`、`visitorName`、`phone`、`visitorScope`、`isRegistered`。
- `POST /api/auth/logout` 成功返回 `{ "loggedOut": true }`，并清除会话 Cookie 和 CSRF Cookie。

## Admin Auth DTO 约定

- Admin auth DTO 对外使用 camelCase 字段。
- `POST /api/admin/auth/login` 请求体为 `{ "username": "admin", "password": "..." }`，成功返回 `AdminMeDTO`。
- 管理员登录请求体拒绝额外字段；前端不能提交 `adminUserId`、`sessionToken`、`csrfToken` 等客户端控制字段。
- `GET /api/admin/auth/me` 已登录管理员返回 `AdminMeDTO`；未登录返回 `401 ADMIN_AUTH_REQUIRED`；游客 session 访问返回 `403 ADMIN_FORBIDDEN`。
- `PATCH /api/admin/auth/profile` 只允许当前管理员修改自己的 `username` 和可选 `newPassword`，必须提交 `currentPassword` 并通过 session-bound CSRF；成功返回 `AdminMeDTO`。
- `AdminMeDTO` 至少包含 `adminUserId`、`username`、`displayName`、`role`。
- 管理员登录失败统一返回 `401 ADMIN_LOGIN_FAILED`，不暴露账号是否存在、密码是否错误或账号是否禁用。
- `POST /api/admin/auth/logout` 只允许管理员 session 调用，成功返回 `{ "loggedOut": true }`，并清除会话 Cookie 和 CSRF Cookie；游客 session 调用返回 `403 ADMIN_FORBIDDEN`，不能误清理游客会话。

## Admin Settings DTO 约定

- `GET /api/admin/settings` 只接受管理员 session，返回系统设置和最近 3 条设置变更日志；这是只读 GET，不要求 CSRF header。
- `PATCH /api/admin/settings` 只接受管理员 session，并且必须携带 CSRF header；请求体只允许提交要修改的设置字段，成功返回最新 `AdminSystemSettingsDTO`。

## Admin Tickets DTO 约定

- `GET /api/admin/tickets` 只接受管理员 session；`POST /api/admin/tickets`、`PATCH /api/admin/tickets/{ticket_id}`、`DELETE /api/admin/tickets/{ticket_id}` 只接受超级管理员 session，并且必须携带 CSRF header。
- 票种保存会同步写入对应日期范围的 `time_slot_quota`，游客端购票日期和时段直接读取这些库存；`slotQuotas[]` 可按 `slotStartTime`、`slotEndTime` 分别设置各销售时段库存，未传时沿用 `slotQuota`。

## Catalog DTO 约定

- Catalog public DTO 对外使用 camelCase 字段。
- `GET /api/catalog/time-slots` 支持 `ticketTypeId`、`visitDate`、`productId` 三个可选查询参数。
- 票品读取失败返回 `503 CATALOG_UNAVAILABLE`；时段读取失败返回 `503 TIME_SLOTS_UNAVAILABLE`，不暴露底层数据库或异常细节。
- 产品 DTO 至少包含 `productId`、`ticketTypeId`、`productName`、`ticketName`、`ticketCategory`、`originalPrice`、`salePrice`、`description`、`startPierName`、`endPierName`。
- 时段 DTO 至少包含 `timeSlotId`、`productId`、`ticketTypeId`、`visitDate`、`slotStartTime`、`slotEndTime`、`quotaRemaining`。
- public DTO 不返回内部 `status`；前端可售态从 public 字段推导，不能依赖内部上下架字段。

## Order DTO 约定

- 游客订单接口使用 camelCase 字段，响应为 `OrderMeDTO`。
- `POST /api/orders` 请求体使用 `buyerName`、`buyerPhone`、`items`。
- `items[]` 请求项使用 `productId`、`timeSlotId`、`visitDate`、`quantity` 和 `passengers[]`；前端不能提交 `visitorId`。
- `passengers[]` 每项使用 `passengerName`、`idType`、`idNumber`、`phone`，可带当前游客自己的 `templateId`；数量必须等于该票项 `quantity`。
- `OrderMeDTO` 至少包含 `orderNo`、`buyerName`、`buyerPhone`、`orderStatus`、`paymentStatus`、`totalAmount`、`payableAmount`、`orderTime`、`items`。
- `items[]` 响应项至少包含 `itemNo`、`productId`、`ticketTypeId`、`productName`、`ticketName`、`timeSlotId`、`visitDate`、`slotStartTime`、`slotEndTime`、`originalPrice`、`finalPrice`、`itemStatus`、`passengerName`、`passengerIdType`、`passengerIdNumberMasked`、`passengerPhoneMasked`；支付后可返回 `ticketCode`；核验分配竹筏后可返回 `raftNo`、`raftSeatNo`、`raftAssignedAt`。
- `totalAmount`、`payableAmount`、`originalPrice`、`finalPrice` 按字符串接收，前端 view model 再转换成数字展示。
- 同一证件在同一票种、同一日期和同一时段只能存在一张未取消票；重复下单返回 `409 PASSENGER_TIME_SLOT_DUPLICATED`。
- `POST /api/orders/{order_no}/pay` 必须传 `Idempotency-Key`；同一次支付尝试必须复用同一个幂等键。
- `POST /api/orders/{order_no}/cancel` 只允许取消当前游客自己的 `CREATED` + `UNPAID` 订单，成功后订单为 `CANCELLED`，明细为 `CANCELLED`。
- `GET /api/me/orders` 支持可选 `status` 查询参数，OpenAPI 必须声明枚举 `CREATED`、`PAID`、`CANCELLED`；非法状态统一返回 `422 ORDER_STATUS_INVALID`。
- 订单详情、支付、取消遇到不存在或非当前游客订单时统一返回 `404 ORDER_NOT_FOUND`，消息为“订单不存在或无权限访问”，响应体不回显订单号。
- 游客订单响应中的 `buyerPhone` 使用脱敏展示，不返回证件号。

## Passenger Template DTO 约定

- `GET /api/me/passenger-templates` 只接受已注册游客 session，返回当前游客自己的常用出行人模板列表。
- `POST /api/me/passenger-templates`、`PATCH /api/me/passenger-templates/{template_id}`、`DELETE /api/me/passenger-templates/{template_id}` 必须校验 session-bound CSRF。
- 模板请求体只允许 `passengerName`、`idType`、`idNumber`、`phone`；当前 `idType` 可使用 `ID_CARD`。
- 同一游客下 `idType + idNumber` 唯一，重复创建或更新为已有证件返回 `409 PASSENGER_TEMPLATE_CONFLICT`。
- 模板接口只能操作当前游客自己的模板；不存在或不属于当前游客时返回 `404 PASSENGER_TEMPLATE_NOT_FOUND`。

## Admin Order DTO 约定

- 后台订单接口只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- `GET /api/admin/orders` 返回 `AdminOrderListDTO`，支持 `status`、`paymentStatus`、`orderNo`、`buyerPhone`、`page`、`pageSize` 查询参数。
- `status` 允许 `CREATED`、`PAID`、`CANCELLED`、`COMPLETED`、`REFUNDING`、`REFUNDED`；非法状态返回 `422 ADMIN_ORDER_STATUS_INVALID`。
- `paymentStatus` 允许 `UNPAID`、`PAID`、`PARTIAL_REFUND`、`REFUNDED`、`FAILED`；非法状态返回 `422 ADMIN_PAYMENT_STATUS_INVALID`。
- `AdminOrderListDTO` 至少包含 `items`、`total`、`page`、`pageSize`。
- `items[]` 列表项为 `AdminOrderSummaryDTO`，至少包含 `orderNo`、`visitorId`、`buyerName`、`buyerPhoneMasked`、`orderStatus`、`paymentStatus`、`totalAmount`、`payableAmount`、`orderTime`、`itemCount`。
- `GET /api/admin/orders/{order_no}` 返回 `AdminOrderDetailDTO`，不存在返回 `404 ADMIN_ORDER_NOT_FOUND`，消息为“订单不存在”。
- 管理员订单 DTO 不复用游客 `OrderMeDTO`，不返回证件号、session token、CSRF token、密码 hash、完整手机号或数据库审计字段。
- 后台订单接口是只读 GET，不要求 CSRF。

## Admin Check-In DTO 约定

- `POST /api/admin/check-ins` 只接受管理员 session，并且必须携带 CSRF header。
- 请求体为 `{ "ticketCode": "TK..." }`，拒绝额外字段；前端不能提交 `adminUserId`、`orderId`、`itemStatus` 或库存字段。
- 只有 `order_status = PAID` 且 `payment_status` 为 `PAID` 或 `PARTIAL_REFUND` 的订单下 `UNUSED` 明细可以核销；已退款明细不能核销。
- 成功后明细变为 `USED`，对应时段 `quotaCheckedIn` 增加 1；订单所有未退款明细都为 `USED` 后订单变为 `COMPLETED`。
- 成功返回 `AdminCheckInDTO`，至少包含 `orderNo`、`itemNo`、`ticketCode`、`orderStatus`、`itemStatus`、`checkedInAt`；核验成功时自动分配竹筏，并可返回 `raftNo`、`raftSeatNo`。
- 票码不存在返回 `404 TICKET_NOT_FOUND`；已核销返回 `409 TICKET_ALREADY_USED`；当前状态不可核销返回 `409 TICKET_NOT_CHECKABLE`。
- 核销响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id 或审计字段。
- 核销成功时必须在同一事务写入 `check_in_audit_log`，操作人来自管理员 session，前端不能提交或覆盖操作人、核销时间或审计动作。

## Admin Batch Check-In DTO 约定

- `POST /api/admin/check-ins/batch` 只接受管理员 session，并且必须携带 CSRF header。
- 请求体为 `{ "ticketCodes": ["TK..."] }`，`ticketCodes` 至少 1 项、最多 50 项；后端会去除首尾空白，并拒绝空票码、重复票码和额外字段。
- 每个票码复用单张核销状态机：只有 `PAID` 订单下 `paymentStatus = PAID/PARTIAL_REFUND` 且明细 `UNUSED` 的票码可以核销；已退款明细不能核销。
- 成功后明细变为 `USED`，对应时段 `quotaCheckedIn` 增加 1；订单所有未退款明细都为 `USED` 后订单变为 `COMPLETED`。
- 成功响应为 `AdminBatchCheckInDTO`，至少包含 `totalCount`、`successCount`、`failureCount`、`results`；`results[]` 每项至少包含 `ticketCode`、`success`，成功项包含 `checkIn`，失败项包含 `code` 和 `message`。
- 逐票业务失败不影响同批其他票码；票码不存在返回结果项 `TICKET_NOT_FOUND`，已核销返回 `TICKET_ALREADY_USED`，当前状态不可核销返回 `TICKET_NOT_CHECKABLE`。
- 未知异常、数据库连接失败或非业务错误仍走统一失败壳，不返回逐票成功壳。
- 成功票码必须在单张核销事务内写入 `check_in_audit_log`；前端不能提交或覆盖操作人、核销时间或审计动作。
- 批量核销响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、`adminUserId` 或 SQL。

## Admin Batch Undo Check-In DTO 约定

- `POST /api/admin/check-ins/batch/undo` 只接受管理员 session，并且必须携带 CSRF header。
- 请求体为 `{ "ticketCodes": ["TK..."], "reason": "..." }`，`ticketCodes` 至少 1 项、最多 50 项；后端会去除首尾空白，并拒绝空票码、重复票码和额外字段。`reason` 可选，trim 后 1-100 字，空字符串、超长值和额外字段返回 `422`。
- 每个票码复用单张撤销核销状态机：只有 `USED` 明细，且订单状态为 `PAID/COMPLETED`、支付状态为 `PAID/PARTIAL_REFUND` 时可以撤销。
- 成功后明细恢复为 `UNUSED`，对应时段 `quotaCheckedIn` 减少 1，且数据库条件保证不会减到负数；若订单原状态为 `COMPLETED`，成功后恢复为 `PAID`。
- 成功响应为 `AdminBatchUndoCheckInDTO`，至少包含 `totalCount`、`successCount`、`failureCount`、`results`；`results[]` 每项至少包含 `ticketCode`、`success`，成功项包含 `undoCheckIn`，失败项包含 `code` 和 `message`。
- 逐票业务失败不影响同批其他票码；票码不存在返回结果项 `TICKET_NOT_FOUND`，票码未核销返回 `TICKET_NOT_CHECKED_IN`，订单或支付状态不允许撤销返回 `TICKET_UNDO_NOT_ALLOWED`。
- 未知异常、数据库连接失败或非业务错误仍走统一失败壳，不返回逐票成功壳。
- 成功票码必须在单张撤销事务内写入 `check_in_audit_log`，`action = UNDO_CHECK_IN`，并保存同批可选 `reason`；业务失败不写成功审计日志，但按失败审计规则写入 `check_in_failure_audit_log`，`action = UNDO_CHECK_IN`。
- 批量撤销核销响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、`adminUserId` 或 SQL。

## Admin Undo Check-In DTO 约定

- `POST /api/admin/check-ins/{ticket_code}/undo` 只接受管理员 session，并且必须携带 CSRF header。
- 请求体可为空；传入时为 `{ "reason": "..." }`。`reason` 可选，trim 后 1-100 字，空字符串、超长值和额外字段返回 `422`；`ticket_code` 来自路径参数，后端会去除首尾空白，不接受前端提交订单状态、明细状态、库存数、操作人或撤销时间。
- 只有 `itemStatus = USED` 的票码可以撤销；订单状态必须为 `PAID` 或 `COMPLETED`，支付状态必须为 `PAID` 或 `PARTIAL_REFUND`。
- 成功后明细恢复为 `UNUSED`，对应时段 `quotaCheckedIn` 减少 1，且数据库条件保证不会减到负数；若订单原状态为 `COMPLETED`，成功后恢复为 `PAID`。
- 成功响应为 `AdminUndoCheckInDTO`，至少包含 `orderNo`、`itemNo`、`ticketCode`、`orderStatus`、`itemStatus`、`undoneAt`。
- 票码不存在返回 `404 TICKET_NOT_FOUND`；票码未核销返回 `409 TICKET_NOT_CHECKED_IN`；订单或支付状态不允许撤销返回 `409 TICKET_UNDO_NOT_ALLOWED`。
- 撤销成功必须在同一事务写入 `check_in_audit_log`，`action = UNDO_CHECK_IN`，并保存可选 `reason`；业务失败不写成功审计日志，但按失败审计规则写入 `check_in_failure_audit_log`，`action = UNDO_CHECK_IN`。
- 撤销核销响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、`adminUserId`、SQL 或审计表内部字段。

## Admin Check-In Audit Log DTO 约定

- `GET /api/admin/check-ins/{ticket_code}/logs` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 成功返回 `AdminCheckInAuditLogDTO[]`，按 `createdAt` 倒序排列，至少包含 `orderNo`、`itemNo`、`ticketCode`、`action`、`reason`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`；`reason` 和 `requestId` 可为 `null`。
- `action` 当前允许 `CHECK_IN` 和 `UNDO_CHECK_IN`；后续新增失败尝试或扫码设备动作时，必须单独扩展动作枚举和状态机。
- 票码不存在返回 `404 TICKET_NOT_FOUND`；票码存在但没有日志时返回空数组。
- 核销审计日志响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、`adminUserId` 或 SQL。

## Admin Check-In Audit Log Search DTO 约定

- `GET /api/admin/check-in-logs` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `ticketCode`、`orderNo`、`operatorUsername`、`reason`、`dateFrom`、`dateTo`、`page`、`pageSize` 查询参数；票码、订单号、操作人用户名和撤销原因均为模糊匹配，日期按审计日志 `createdAt` 的日期筛选。
- `dateFrom > dateTo` 返回 `422 ADMIN_CHECK_IN_LOG_DATE_RANGE_INVALID`。
- 成功返回 `AdminCheckInAuditLogListDTO`，至少包含 `items`、`total`、`page`、`pageSize`；`items[]` 至少包含 `orderNo`、`itemNo`、`ticketCode`、`action`、`reason`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`，按 `createdAt` 倒序排列。
- 核销审计日志检索响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、`adminUserId` 或 SQL。

## Admin Check-In Failure Audit Log Search DTO 约定

- `GET /api/admin/check-in-failure-logs` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `ticketCode`、`failureCode`、`operatorUsername`、`dateFrom`、`dateTo`、`page`、`pageSize` 查询参数；票码和操作人用户名为模糊匹配，日期按失败审计日志 `createdAt` 的日期筛选。
- `failureCode` 只允许 `TICKET_NOT_FOUND`、`TICKET_ALREADY_USED`、`TICKET_NOT_CHECKABLE`、`TICKET_NOT_CHECKED_IN`、`TICKET_UNDO_NOT_ALLOWED`；非法值返回 `422 ADMIN_CHECK_IN_FAILURE_CODE_INVALID`。
- `dateFrom > dateTo` 返回 `422 ADMIN_CHECK_IN_FAILURE_LOG_DATE_RANGE_INVALID`。
- 成功返回 `AdminCheckInFailureAuditLogListDTO`，至少包含 `items`、`total`、`page`、`pageSize`；`items[]` 至少包含 `ticketCode`、`action`、`failureCode`、`failureMessage`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`。
- 仅记录管理员 session 与 CSRF 校验通过后的核销/撤销核销业务失败尝试；匿名、游客、CSRF 失败和系统异常不写入业务失败审计。
- 核销失败审计检索响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、订单内部 id、`adminUserId` 或 SQL。

## Admin Check-In Failure Audit Log CSV Export 约定

- `GET /api/admin/check-in-failure-logs.csv` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- CSV 导出支持可选 `ticketCode`、`failureCode`、`operatorUsername`、`dateFrom`、`dateTo` 查询参数；筛选语义与 `GET /api/admin/check-in-failure-logs` 一致。
- `failureCode` 只允许 `TICKET_NOT_FOUND`、`TICKET_ALREADY_USED`、`TICKET_NOT_CHECKABLE`、`TICKET_NOT_CHECKED_IN`、`TICKET_UNDO_NOT_ALLOWED`；非法值返回 `422 ADMIN_CHECK_IN_FAILURE_CODE_INVALID`。
- `dateFrom > dateTo` 返回 `422 ADMIN_CHECK_IN_FAILURE_LOG_DATE_RANGE_INVALID`。
- 成功响应是 CSV 文件，不是统一 JSON 成功壳；`Content-Type` 为 `text/csv; charset=utf-8`，`Content-Disposition` 使用 `attachment; filename="admin-check-in-failure-logs-<start>-<end>.csv"` 下载文件名，未传日期时对应位置使用 `start` 或 `end`。
- 跨域前端可读取 CORS 暴露的 `Content-Disposition` 响应头来获得下载文件名。
- CSV 列固定为 `ticketCode`、`action`、`failureCode`、`failureMessage`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`。
- CSV 单元格必须防护公式注入，不能让 `=`、`+`、`-`、`@`、制表符、回车、换行或前导空格后危险字符开头的值原样作为公式进入表格软件。
- CSV 不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、订单内部 id、`adminUserId` 或 SQL。

## Admin Check-In Failure Audit Log XLSX Export 约定

- `GET /api/admin/check-in-failure-logs.xlsx` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- XLSX 导出支持可选 `ticketCode`、`failureCode`、`operatorUsername`、`dateFrom`、`dateTo` 查询参数；筛选语义与 `GET /api/admin/check-in-failure-logs` 一致。
- `failureCode` 只允许 `TICKET_NOT_FOUND`、`TICKET_ALREADY_USED`、`TICKET_NOT_CHECKABLE`、`TICKET_NOT_CHECKED_IN`、`TICKET_UNDO_NOT_ALLOWED`；非法值返回 `422 ADMIN_CHECK_IN_FAILURE_CODE_INVALID`。
- `dateFrom > dateTo` 返回 `422 ADMIN_CHECK_IN_FAILURE_LOG_DATE_RANGE_INVALID`。
- 成功响应是 XLSX 文件，不是统一 JSON 成功壳；`Content-Type` 为 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，`Content-Disposition` 使用 `attachment; filename="admin-check-in-failure-logs-<start>-<end>.xlsx"` 下载文件名，未传日期时对应位置使用 `start` 或 `end`。
- 跨域前端可读取 CORS 暴露的 `Content-Disposition` 响应头来获得下载文件名。
- XLSX 列固定为 `ticketCode`、`action`、`failureCode`、`failureMessage`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`。
- XLSX 单元格必须写为 inline string，不生成公式节点；所有可控文本都要防护公式注入，不能让 `=`、`+`、`-`、`@`、制表符、回车、换行或前导空格后危险字符开头的值原样作为公式进入表格软件。
- 写入 XML 前必须清理 XML 1.0 非法控制字符，避免生成损坏的 workbook。
- XLSX 不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、订单内部 id、`adminUserId` 或 SQL。

## Admin Check-In Audit Log CSV Export 约定

- `GET /api/admin/check-in-logs.csv` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- CSV 导出支持可选 `ticketCode`、`orderNo`、`operatorUsername`、`reason`、`dateFrom`、`dateTo` 查询参数；筛选语义与 `GET /api/admin/check-in-logs` 一致。
- `dateFrom > dateTo` 返回 `422 ADMIN_CHECK_IN_LOG_DATE_RANGE_INVALID`。
- 成功响应是 CSV 文件，不是统一 JSON 成功壳；`Content-Type` 为 `text/csv; charset=utf-8`，`Content-Disposition` 使用 `attachment; filename="admin-check-in-logs-<start>-<end>.csv"` 下载文件名，未传日期时对应位置使用 `start` 或 `end`。
- 跨域前端可读取 CORS 暴露的 `Content-Disposition` 响应头来获得下载文件名。
- CSV 列固定为 `orderNo`、`itemNo`、`ticketCode`、`action`、`reason`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`。
- CSV 单元格必须防护公式注入，不能让 `=`、`+`、`-`、`@`、制表符、回车、换行或前导空格后危险字符开头的值原样作为公式进入表格软件。
- CSV 不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、`adminUserId` 或 SQL。

## Admin Check-In Audit Log XLSX Export 约定

- `GET /api/admin/check-in-logs.xlsx` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- XLSX 导出支持可选 `ticketCode`、`orderNo`、`operatorUsername`、`reason`、`dateFrom`、`dateTo` 查询参数；筛选语义与 `GET /api/admin/check-in-logs` 一致。
- `dateFrom > dateTo` 返回 `422 ADMIN_CHECK_IN_LOG_DATE_RANGE_INVALID`。
- 成功响应是 XLSX 文件，不是统一 JSON 成功壳；`Content-Type` 为 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，`Content-Disposition` 使用 `attachment; filename="admin-check-in-logs-<start>-<end>.xlsx"` 下载文件名，未传日期时对应位置使用 `start` 或 `end`。
- 跨域前端可读取 CORS 暴露的 `Content-Disposition` 响应头来获得下载文件名。
- XLSX 列固定为 `orderNo`、`itemNo`、`ticketCode`、`action`、`reason`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`。
- XLSX 单元格必须写为字符串，不生成公式节点；必须防护公式注入，不能让 `=`、`+`、`-`、`@`、制表符、回车、换行或前导空格后危险字符开头的值原样作为公式进入表格软件。
- XLSX 写入 XML 前必须清理 XML 1.0 非法控制字符。
- XLSX 不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、`adminUserId` 或 SQL。

## Admin Refund DTO 约定

- `POST /api/admin/orders/{order_no}/refund` 只接受 `SUPER_ADMIN` 管理员 session，并且必须携带 CSRF header；`OPERATOR` 返回 `403 ADMIN_FORBIDDEN`，且不会产生订单、库存、支付或退款审计副作用。
- 请求体为 `{ "reason": "..." }`，`reason` 可选，最多 100 字符；请求体拒绝额外字段。
- 只允许 `PAID + PAID`、所有明细为 `UNUSED`，且存在 `SUCCESS` 支付记录的订单执行整单模拟退款。
- 成功后订单和支付状态变为 `REFUNDED`，明细变为 `REFUNDED`，`paidAmount` 归零，并按票数回补 `quotaSold`。
- 成功返回 `AdminRefundDTO`，至少包含 `orderNo`、`orderStatus`、`paymentStatus`、`refundedAmount`、`refundedItemCount`、`refundedAt`。
- 订单不存在返回 `404 ADMIN_ORDER_NOT_FOUND`；已退款返回 `409 ORDER_ALREADY_REFUNDED`；不可退款返回 `409 ORDER_NOT_REFUNDABLE`。
- 退款响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id 或审计字段。

## Admin Partial Refund DTO 约定

- `POST /api/admin/orders/{order_no}/refund/items` 只接受 `SUPER_ADMIN` 管理员 session，并且必须携带 CSRF header；`OPERATOR` 返回 `403 ADMIN_FORBIDDEN`，且不会产生订单、库存、支付或退款审计副作用。
- 请求体为 `{ "itemNos": ["..."], "reason": "..." }`，`itemNos` 至少 1 项、最多 20 项，拒绝空票项号和重复票项号；`reason` 可选，最多 100 字符；请求体拒绝额外字段。
- 只允许 `order_status = PAID`、`payment_status` 为 `PAID` 或 `PARTIAL_REFUND`、订单内非退款票项均为 `UNUSED`，且被选中票项为 `UNUSED` 的订单执行部分模拟退款。
- 退款金额由后端根据锁定后的订单明细 `finalPrice` 计算，前端不能提交退款金额、订单状态、支付状态或库存数量。
- 成功后所选明细变为 `REFUNDED`，并按所选票项回补 `quotaSold`；若仍有未退款票项，订单保持 `PAID` 且支付状态变为 `PARTIAL_REFUND`；若所有票项均已退款，订单和支付状态变为 `REFUNDED`。
- 成功返回 `AdminPartialRefundDTO`，至少包含 `orderNo`、`orderStatus`、`paymentStatus`、`refundedAmount`、`refundedItemCount`、`refundedItemNos`、`refundedAt`。
- 订单不存在返回 `404 ADMIN_ORDER_NOT_FOUND`；已退款返回 `409 ORDER_ALREADY_REFUNDED`；票项不属于该订单返回 `409 ORDER_REFUND_ITEMS_INVALID`；状态不可部分退款返回 `409 ORDER_NOT_PARTIALLY_REFUNDABLE`。
- 部分退款响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id 或审计字段。

## Admin Refund Audit Log DTO 约定

- `GET /api/admin/orders/{order_no}/refund-logs` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 成功返回 `AdminRefundAuditLogDTO[]`，按 `createdAt` 倒序排列，至少包含 `orderNo`、`refundType`、`refundedAmount`、`refundedItemCount`、`refundedItemNos`、`reason`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`；`reason` 和 `requestId` 可为 `null`。
- `refundType` 只允许 `FULL` 或 `PARTIAL`；审计日志必须由后端退款事务写入，前端不能提交操作人、退款金额、退款状态或审计时间。
- 订单不存在返回 `404 ADMIN_ORDER_NOT_FOUND`；订单存在但没有退款日志时返回空数组。
- 退款审计日志响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、`adminUserId` 或 SQL。

## Admin Refund Audit Log Search DTO 约定

- `GET /api/admin/refund-logs` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `refundType`、`orderNo`、`operatorUsername`、`dateFrom`、`dateTo`、`page`、`pageSize` 查询参数；`refundType` 只允许 `FULL` 或 `PARTIAL`。
- `dateFrom > dateTo` 返回 `422 ADMIN_REFUND_LOG_DATE_RANGE_INVALID`；非法 `refundType` 返回 `422 ADMIN_REFUND_LOG_TYPE_INVALID`。
- 成功返回 `AdminRefundAuditLogListDTO`，至少包含 `items`、`total`、`page`、`pageSize`；`items[]` 为 `AdminRefundAuditLogDTO`，按 `createdAt` 倒序排列。
- 退款审计日志检索响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、`adminUserId` 或 SQL。

## Admin Refund Audit Log CSV Export 约定

- `GET /api/admin/refund-logs.csv` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `refundType`、`orderNo`、`operatorUsername`、`dateFrom`、`dateTo` 查询参数；筛选语义与 `GET /api/admin/refund-logs` 一致，`refundType` 只允许 `FULL` 或 `PARTIAL`。
- `dateFrom > dateTo` 返回 `422 ADMIN_REFUND_LOG_DATE_RANGE_INVALID`；非法 `refundType` 返回 `422 ADMIN_REFUND_LOG_TYPE_INVALID`。
- 成功响应是 CSV 文件，不是统一 JSON 成功壳；`Content-Type` 为 `text/csv; charset=utf-8`，`Content-Disposition` 使用 `attachment` 下载文件名。
- CSV 列固定为 `orderNo`、`refundType`、`refundedAmount`、`refundedItemCount`、`refundedItemNos`、`reason`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`。
- CSV 单元格必须防护公式注入，不能让 `=`、`+`、`-`、`@`、制表符、回车、换行或前导空格后危险字符开头的值原样作为公式进入表格软件。
- CSV 不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、`adminUserId` 或 SQL。

## Admin Refund Audit Log XLSX Export 约定

- `GET /api/admin/refund-logs.xlsx` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `refundType`、`orderNo`、`operatorUsername`、`dateFrom`、`dateTo` 查询参数；筛选语义与 `GET /api/admin/refund-logs` 一致，`refundType` 只允许 `FULL` 或 `PARTIAL`。
- `dateFrom > dateTo` 返回 `422 ADMIN_REFUND_LOG_DATE_RANGE_INVALID`；非法 `refundType` 返回 `422 ADMIN_REFUND_LOG_TYPE_INVALID`。
- 成功响应是 XLSX 文件，不是统一 JSON 成功壳；`Content-Type` 为 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，`Content-Disposition` 使用 `attachment; filename="admin-refund-logs-<start>-<end>.xlsx"` 下载文件名，未传日期时对应位置使用 `start` 或 `end`。
- XLSX 列固定为 `orderNo`、`refundType`、`refundedAmount`、`refundedItemCount`、`refundedItemNos`、`reason`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`。
- XLSX 单元格必须写为字符串，不生成公式节点；必须防护公式注入，不能让 `=`、`+`、`-`、`@`、制表符、回车、换行或前导空格后危险字符开头的值原样作为公式进入表格软件。
- XLSX 写入 XML 前必须清理 XML 1.0 非法控制字符。
- XLSX 不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、`adminUserId` 或 SQL。

## Admin Report Summary DTO 约定

- `GET /api/admin/reports/summary` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `dateFrom`、`dateTo` 查询参数，按订单创建日期过滤；`dateFrom > dateTo` 返回 `422 ADMIN_REPORT_DATE_RANGE_INVALID`。
- 成功返回 `AdminReportSummaryDTO`，至少包含 `dateFrom`、`dateTo`、`orderCount`、`paidOrderCount`、`completedOrderCount`、`refundedOrderCount`、`cancelledOrderCount`、`netPaidAmount`、`ticketCount`、`soldTicketCount`、`checkedInTicketCount`、`refundedTicketCount`。
- 报表响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id 或审计字段。

## Admin Payment Reconciliation DTO 约定

- `GET /api/admin/reports/payment-reconciliation` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `dateFrom`、`dateTo` 查询参数，按订单创建日期过滤；`dateFrom > dateTo` 返回 `422 ADMIN_REPORT_DATE_RANGE_INVALID`。
- 成功返回 `AdminPaymentReconciliationDTO`，至少包含 `dateFrom`、`dateTo`、`orderNetPaidAmount`、`capturedPaymentAmount`、`refundAuditAmount`、`expectedNetAmount`、`unreconciledAmount`、`capturedPaymentCount`、`refundAuditLogCount`、`reconciled`。
- `capturedPaymentAmount` 统计 `payment_record.payment_status IN ('SUCCESS', 'REFUNDED')` 的原始收款金额；`refundAuditAmount` 统计同一订单范围内退款审计金额；`expectedNetAmount = capturedPaymentAmount - refundAuditAmount`；`unreconciledAmount = orderNetPaidAmount - expectedNetAmount`。
- 对账响应不返回完整手机号、证件号、支付流水号、渠道交易号、session token、CSRF token、密码 hash、数据库内部 id、SQL、审计明细或内部审计字段。

## Admin Payment Reconciliation CSV Export 约定

- `GET /api/admin/reports/payment-reconciliation.csv` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `dateFrom`、`dateTo` 查询参数，按订单创建日期过滤；`dateFrom > dateTo` 返回 `422 ADMIN_REPORT_DATE_RANGE_INVALID`。
- 成功响应是 CSV 文件，不是统一 JSON 成功壳；`Content-Type` 为 `text/csv; charset=utf-8`，`Content-Disposition` 使用 `attachment; filename="admin-payment-reconciliation-<start>-<end>.csv"`。
- CSV 列固定为 `dateFrom`、`dateTo`、`orderNetPaidAmount`、`capturedPaymentAmount`、`refundAuditAmount`、`expectedNetAmount`、`unreconciledAmount`、`capturedPaymentCount`、`refundAuditLogCount`、`reconciled`。
- CSV 对账导出不返回完整手机号、证件号、支付流水号、渠道交易号、session token、CSRF token、密码 hash、数据库内部 id、SQL、审计明细或内部审计字段，并复用表格公式注入防护。

## Admin Payment Reconciliation XLSX Export 约定

- `GET /api/admin/reports/payment-reconciliation.xlsx` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `dateFrom`、`dateTo` 查询参数，按订单创建日期过滤；`dateFrom > dateTo` 返回 `422 ADMIN_REPORT_DATE_RANGE_INVALID`。
- 成功响应是 XLSX 文件，不是统一 JSON 成功壳；`Content-Type` 为 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，`Content-Disposition` 使用 `attachment; filename="admin-payment-reconciliation-<start>-<end>.xlsx"`。
- XLSX 列固定为 `dateFrom`、`dateTo`、`orderNetPaidAmount`、`capturedPaymentAmount`、`refundAuditAmount`、`expectedNetAmount`、`unreconciledAmount`、`capturedPaymentCount`、`refundAuditLogCount`、`reconciled`，与 CSV 导出一致。
- XLSX 对账导出不返回完整手机号、证件号、支付流水号、渠道交易号、session token、CSRF token、密码 hash、数据库内部 id、SQL、审计明细或内部审计字段；单元格写成 inline string，不生成公式节点，并清理 XML 1.0 非法控制字符。

## Admin Product Breakdown DTO 约定

- `GET /api/admin/reports/product-breakdown` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `dateFrom`、`dateTo` 查询参数，按订单创建日期过滤；`dateFrom > dateTo` 返回 `422 ADMIN_REPORT_DATE_RANGE_INVALID`。
- 成功返回 `AdminProductBreakdownDTO[]`，每一行按产品和票种分组，至少包含 `productId`、`ticketTypeId`、`productName`、`ticketName`、`orderCount`、`ticketCount`、`soldTicketCount`、`checkedInTicketCount`、`refundedTicketCount`、`netPaidAmount`。
- `orderCount` 按去重订单数统计；`netPaidAmount` 按 `UNUSED` 和 `USED` 明细的 `finalPrice` 汇总，不能用订单金额 join 后放大。
- 产品维度报表响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、SQL 或审计字段。

## Admin Product Breakdown CSV Export 约定

- `GET /api/admin/reports/product-breakdown.csv` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `dateFrom`、`dateTo` 查询参数，按订单创建日期过滤；`dateFrom > dateTo` 返回 `422 ADMIN_REPORT_DATE_RANGE_INVALID`。
- 成功响应是 CSV 文件，不是统一 JSON 成功壳；`Content-Type` 为 `text/csv; charset=utf-8`，`Content-Disposition` 使用 `attachment; filename="admin-product-breakdown-<start>-<end>.csv"`。
- CSV 列固定为 `productId`、`ticketTypeId`、`productName`、`ticketName`、`orderCount`、`ticketCount`、`soldTicketCount`、`checkedInTicketCount`、`refundedTicketCount`、`netPaidAmount`。
- CSV 产品维度导出不返回买家个人信息、支付流水号、渠道交易号、session token、CSRF token、密码 hash、SQL、审计明细或内部审计字段，并复用表格公式注入防护。

## Admin Product Breakdown XLSX Export 约定

- `GET /api/admin/reports/product-breakdown.xlsx` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `dateFrom`、`dateTo` 查询参数，按订单创建日期过滤；`dateFrom > dateTo` 返回 `422 ADMIN_REPORT_DATE_RANGE_INVALID`。
- 成功响应是 XLSX 文件，不是统一 JSON 成功壳；`Content-Type` 为 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，`Content-Disposition` 使用 `attachment; filename="admin-product-breakdown-<start>-<end>.xlsx"`。
- XLSX 列固定为 `productId`、`ticketTypeId`、`productName`、`ticketName`、`orderCount`、`ticketCount`、`soldTicketCount`、`checkedInTicketCount`、`refundedTicketCount`、`netPaidAmount`，与 CSV 导出一致。
- XLSX 产品维度导出不返回买家个人信息、支付流水号、渠道交易号、session token、CSRF token、密码 hash、SQL、审计明细或内部审计字段；单元格写成 inline string，不生成公式节点，并清理 XML 1.0 非法控制字符。

## Admin Daily Trend DTO 约定

- `GET /api/admin/reports/daily-trend` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `dateFrom`、`dateTo`、`includeEmpty` 查询参数，按订单创建日期过滤；`dateFrom > dateTo` 返回 `422 ADMIN_REPORT_DATE_RANGE_INVALID`。
- 成功返回 `AdminDailyTrendDTO[]`，每一行按 `reportDate` 聚合，至少包含 `reportDate`、`orderCount`、`paidOrderCount`、`completedOrderCount`、`refundedOrderCount`、`cancelledOrderCount`、`netPaidAmount`、`ticketCount`、`soldTicketCount`、`checkedInTicketCount`、`refundedTicketCount`。
- 默认只返回有订单活动的日期；`includeEmpty=true` 时必须同时提供 `dateFrom` 和 `dateTo`，最多补 366 天，缺少边界返回 `422 ADMIN_REPORT_INCLUDE_EMPTY_RANGE_REQUIRED`，范围过大返回 `422 ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE`。
- 日报趋势金额聚合与明细票数聚合必须分开，不能让订单金额因明细 join 被重复放大。
- 日报趋势响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、SQL 或审计字段。

## Admin Hourly Trend DTO 约定

- `GET /api/admin/reports/hourly-trend` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `dateFrom`、`dateTo`、`includeEmpty` 查询参数，按订单创建日期过滤；`dateFrom > dateTo` 返回 `422 ADMIN_REPORT_DATE_RANGE_INVALID`。
- 成功返回 `AdminHourlyTrendDTO[]`，每一行按 `reportHour` 聚合，`reportHour` 格式为 `YYYY-MM-DDTHH:00:00`，至少包含 `reportHour`、`orderCount`、`paidOrderCount`、`completedOrderCount`、`refundedOrderCount`、`cancelledOrderCount`、`netPaidAmount`、`ticketCount`、`soldTicketCount`、`checkedInTicketCount`、`refundedTicketCount`。
- 默认只返回有订单活动的小时；`includeEmpty=true` 时必须同时提供 `dateFrom` 和 `dateTo`，最多补 31 天内的小时，缺少边界返回 `422 ADMIN_REPORT_INCLUDE_EMPTY_RANGE_REQUIRED`，范围过大返回 `422 ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE`。
- 小时趋势金额聚合与明细票数聚合必须分开，不能让订单金额因明细 join 被重复放大。
- 小时趋势响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、SQL 或审计字段。

## Admin Monthly Trend DTO 约定

- `GET /api/admin/reports/monthly-trend` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `dateFrom`、`dateTo`、`includeEmpty` 查询参数，按订单创建日期过滤；`dateFrom > dateTo` 返回 `422 ADMIN_REPORT_DATE_RANGE_INVALID`。
- 成功返回 `AdminMonthlyTrendDTO[]`，每一行按 `reportMonth` 聚合，`reportMonth` 格式为 `YYYY-MM`，至少包含 `reportMonth`、`orderCount`、`paidOrderCount`、`completedOrderCount`、`refundedOrderCount`、`cancelledOrderCount`、`netPaidAmount`、`ticketCount`、`soldTicketCount`、`checkedInTicketCount`、`refundedTicketCount`。
- 默认只返回有订单活动的月份；`includeEmpty=true` 时必须同时提供 `dateFrom` 和 `dateTo`，最多补 60 个月，缺少边界返回 `422 ADMIN_REPORT_INCLUDE_EMPTY_RANGE_REQUIRED`，范围过大返回 `422 ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE`。
- 月度趋势金额聚合与明细票数聚合必须分开，不能让订单金额因明细 join 被重复放大。
- 月度趋势响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、SQL 或审计字段。

## Admin Trend CSV Export 约定

- `GET /api/admin/reports/daily-trend.csv`、`GET /api/admin/reports/hourly-trend.csv`、`GET /api/admin/reports/monthly-trend.csv` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `dateFrom`、`dateTo`、`includeEmpty` 查询参数，语义和对应 JSON 趋势接口一致；`dateFrom > dateTo` 返回 `422 ADMIN_REPORT_DATE_RANGE_INVALID`。
- `includeEmpty=true` 时必须同时提供 `dateFrom` 和 `dateTo`；日报最多补 366 天，小时最多补 31 天内的小时，月报最多补 60 个月；缺少边界返回 `422 ADMIN_REPORT_INCLUDE_EMPTY_RANGE_REQUIRED`，范围过大返回 `422 ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE`。
- 成功响应是 CSV 文件，不是统一 JSON 成功壳；`Content-Type` 为 `text/csv; charset=utf-8`，`Content-Disposition` 使用 `attachment; filename="admin-<daily|hourly|monthly>-trend-<start>-<end>.csv"`。
- CSV 列分别以 `reportDate`、`reportHour` 或 `reportMonth` 开头，后续指标固定为 `orderCount`、`paidOrderCount`、`completedOrderCount`、`refundedOrderCount`、`cancelledOrderCount`、`netPaidAmount`、`ticketCount`、`soldTicketCount`、`checkedInTicketCount`、`refundedTicketCount`。
- CSV 单元格必须防护公式注入，不能让 `=`、`+`、`-`、`@`、制表符、回车、换行或前导空格后危险字符开头的值原样作为公式进入表格软件。
- 趋势 CSV 不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、SQL 或审计字段。

## Admin Trend XLSX Export 约定

- `GET /api/admin/reports/daily-trend.xlsx`、`GET /api/admin/reports/hourly-trend.xlsx`、`GET /api/admin/reports/monthly-trend.xlsx` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `dateFrom`、`dateTo`、`includeEmpty` 查询参数，语义和对应 JSON 趋势接口一致；`dateFrom > dateTo` 返回 `422 ADMIN_REPORT_DATE_RANGE_INVALID`。
- `includeEmpty=true` 时必须同时提供 `dateFrom` 和 `dateTo`；日报最多补 366 天，小时最多补 31 天内的小时，月报最多补 60 个月；缺少边界返回 `422 ADMIN_REPORT_INCLUDE_EMPTY_RANGE_REQUIRED`，范围过大返回 `422 ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE`。
- 成功响应是 XLSX 文件，不是统一 JSON 成功壳；`Content-Type` 为 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，`Content-Disposition` 使用 `attachment; filename="admin-<daily|hourly|monthly>-trend-<start>-<end>.xlsx"`。
- XLSX 列分别以 `reportDate`、`reportHour` 或 `reportMonth` 开头，后续指标与趋势 CSV 完全一致。
- XLSX 单元格必须写成字符串单元格，不生成公式节点；危险公式开头或前导空格后危险字符开头的文本继续加单引号。
- XLSX worksheet 文本必须移除 XML 1.0 非法控制字符。
- 趋势 XLSX 不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、SQL 或审计字段。

## Admin Order CSV Export 约定

- `GET /api/admin/reports/orders.csv` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `dateFrom`、`dateTo` 查询参数，按订单创建日期过滤；`dateFrom > dateTo` 返回 `422 ADMIN_REPORT_DATE_RANGE_INVALID`。
- 成功响应是 CSV 文件，不是统一 JSON 成功壳；`Content-Type` 为 `text/csv; charset=utf-8`，`Content-Disposition` 使用 `attachment` 下载文件名。
- CSV 列固定为 `orderNo`、`buyerName`、`buyerPhoneMasked`、`orderStatus`、`paymentStatus`、`totalAmount`、`payableAmount`、`orderTime`、`itemCount`。
- CSV 单元格必须防护公式注入，不能让 `=`、`+`、`-`、`@`、制表符、回车、换行或前导空格后危险字符开头的值原样作为公式进入表格软件。
- CSV 不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、SQL 或审计字段。

## Admin Order XLSX Export 约定

- `GET /api/admin/reports/orders.xlsx` 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持可选 `dateFrom`、`dateTo` 查询参数，按订单创建日期过滤；`dateFrom > dateTo` 返回 `422 ADMIN_REPORT_DATE_RANGE_INVALID`。
- 成功响应是 XLSX 文件，不是统一 JSON 成功壳；`Content-Type` 为 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，`Content-Disposition` 使用 `attachment` 下载文件名。
- XLSX 列固定为 `orderNo`、`buyerName`、`buyerPhoneMasked`、`orderStatus`、`paymentStatus`、`totalAmount`、`payableAmount`、`orderTime`、`itemCount`，与 CSV 导出一致。
- XLSX 单元格必须写成字符串单元格，不生成公式节点；危险公式开头或前导空格后危险字符开头的文本继续加单引号。
- XLSX worksheet 文本必须移除 XML 1.0 非法控制字符，不能因为单条脏数据生成不可解析的工作簿。
- XLSX 不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、SQL 或审计字段。

## Mock Payment Callback DTO 约定

- `POST /api/payments/mock/callback` 是模拟第三方支付成功回调，不接受游客 session，也不要求 CSRF header。
- 该回调只对应 `PAYMENT_PROVIDER=mock`；真实支付渠道回调、渠道交易号验签、退款通知和结算文件尚未接入，不能通过改环境变量启用。
- 必须携带 `X-Mockpay-Timestamp` 与 `X-Mockpay-Signature`；签名为 `HMAC-SHA256(timestamp + "." + raw_body)` 的十六进制摘要。
- 请求体至少包含 `eventId`、`orderNo`、`paymentNo`、`transactionNo`、`paidAmount`、`paymentStatus`；本切片只接受 `paymentStatus = SUCCESS`。
- 合法回调复用支付状态机：只允许 `CREATED + UNPAID` 且明细为 `PENDING_PAYMENT` 的订单支付成功，扣减库存、写支付记录、生成票码并把订单置为 `PAID + PAID`。
- `eventId` 必须幂等，重复回调不能重复扣库存或出票。
- 成功返回 `MockPaymentCallbackDTO`，至少包含 `eventId`、`orderNo`、`orderStatus`、`paymentStatus`、`idempotent`、`processedAt`。
- 签名错误返回 `401 MOCKPAY_SIGNATURE_INVALID`；时间戳过期返回 `401 MOCKPAY_TIMESTAMP_INVALID`；事件不合法返回 `422 MOCKPAY_EVENT_INVALID`；订单不存在返回 `404 MOCKPAY_ORDER_NOT_FOUND`；金额不匹配返回 `409 MOCKPAY_AMOUNT_MISMATCH`。
- 回调响应和错误响应不返回签名密钥、原始签名、完整请求体、完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、SQL 或堆栈。

## 响应格式

成功：

```json
{
  "success": true,
  "data": {},
  "request_id": "..."
}
```

- 除明确标记为文件下载的接口外，所有成功响应都必须保持 `success`、`data`、`request_id` 三个顶层字段，便于前端统一解析 `ApiSuccess<T>`。
- 响应体 `request_id` 必须与响应头 `x-request-id` 一致；请求不带 `x-request-id` 时服务端生成非空 id。
- 已实现 JSON 接口的 OpenAPI 200 响应必须声明为 `ApiSuccessDTO<T>`，其中 `data` 指向对应的前端 DTO 或 DTO 列表；文件下载接口必须声明实际媒体类型。
- 已实现接口的 OpenAPI 响应必须声明 `x-request-id` 响应头。

失败：

```json
{
  "success": false,
  "code": "ERROR_CODE",
  "message": "用户可理解的错误信息",
  "request_id": "..."
}
```

- 所有失败响应都必须保持 `success`、`code`、`message`、`request_id` 四个顶层字段，便于前端统一构造 `ApiError`。
- 响应体 `request_id` 必须与响应头 `x-request-id` 一致；请求带 `x-request-id` 时服务端原样回传。
- FastAPI/Pydantic 请求体验证失败统一返回 `422 VALIDATION_ERROR`，不把框架默认的 `detail`、字段路径、原始输入或堆栈返回给前端。
- 已实现接口的 OpenAPI 错误响应必须声明为 `ApiFailureDTO`，不能暴露 FastAPI 默认 `HTTPValidationError.detail` 结构。
- 已实现接口的 OpenAPI 错误响应必须声明 `x-request-id` 响应头。
- 前端联调需要离线契约时，使用 `scripts/export-openapi.py` 导出当前后端 OpenAPI JSON。

## DTO 原则

- 公共接口使用 public DTO。
- 游客接口使用 me DTO。
- 管理员接口后续使用 admin DTO。
- 内部数据库行不直接响应给前端。
