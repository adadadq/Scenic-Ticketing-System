# 后台撤销核销原因审计设计

日期：2026-07-01

## 问题定义

后台已经支持单张和批量撤销核销，并把成功撤销写入 `check_in_audit_log`。但审计日志目前只能看到谁在什么时候撤销了哪张票，不能解释为什么撤销。现场复盘、误核销排查和安全审查需要把撤销原因和成功撤销动作绑定在一起。

## 边界

本切片实现：

- `POST /api/admin/check-ins/{ticketCode}/undo` 支持可选请求体 `{ "reason": "..." }`。
- `POST /api/admin/check-ins/batch/undo` 支持可选 `reason`，同批成功撤销票码共享同一个原因。
- `reason` 经过 trim，长度 1-100 字；空字符串、超长和额外字段返回 `422`。
- 成功撤销写入 `check_in_audit_log.reason`；普通核销写入 `NULL`。
- 核销审计日志详情、全局检索、CSV 导出和 XLSX 导出返回 `reason`。
- 新增幂等迁移，给已有运行库补 `check_in_audit_log.reason`。

本切片不实现：

- 强制填写撤销原因。
- 撤销审批流、二次确认或撤销权限分级。
- 把原因写入失败尝试审计表。
- 按原因筛选审计日志。
- 改动前端页面交互。

## API 契约

单张撤销：

```text
POST /api/admin/check-ins/TK-USED/undo
Content-Type: application/json

{ "reason": "现场误核销" }
```

批量撤销：

```text
POST /api/admin/check-ins/batch/undo
Content-Type: application/json

{ "ticketCodes": ["TK-1", "TK-2"], "reason": "批量误核销" }
```

兼容性：

- 单张撤销不传 body 时仍按无原因撤销。
- 批量撤销不传 `reason` 时仍按无原因撤销。
- 响应 DTO 不额外返回 reason，原因通过审计日志查询和导出读取。

## 安全边界

- 撤销接口仍要求管理员 session 和 session-bound CSRF。
- 前端不能提交或覆盖操作人、撤销时间、审计动作或 request id。
- `reason` 只作为审计文本保存，不参与 SQL 拼接。
- 审计日志 DTO 和导出仍不返回手机号、证件号、session、CSRF、密码 hash、内部 id 或 `adminUserId`。
- CSV/XLSX 导出中的 `reason` 继续走公式注入防护；XLSX 继续写 inline string 并清理 XML 1.0 非法控制字符。

## 数据流

1. Router 接收撤销请求和可选 reason。
2. Pydantic DTO trim 并校验 reason。
3. Service 生成 `AdminCheckInAuditInput`，把 reason 带入成功撤销审计。
4. Repository 在成功撤销事务内写入 `check_in_audit_log.reason`。
5. 审计日志读取和导出从 `check_in_audit_log.reason` 返回安全字段。

## 验收

- 单张撤销可记录 trim 后的 reason，并在票码审计日志中返回。
- 批量撤销成功票码共享同一 reason，失败票码不写成功审计日志。
- 空 reason、超长 reason 和额外字段返回 `422`，不发生撤销。
- 迁移 SQL 使用 `ADD COLUMN IF NOT EXISTS reason VARCHAR(100)`。
- Postgres 插入审计日志时 reason 进入 SQL 参数，不拼接进 SQL。
- CSV/XLSX 导出包含 `reason`，并继续覆盖公式注入防护和 XML 控制字符清洗。
