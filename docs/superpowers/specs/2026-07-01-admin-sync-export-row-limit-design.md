# 后台同步导出行数上限设计

日期：2026-07-01

## 问题

后台已经支持订单、核销审计、核销失败审计、退款审计、支付对账、产品维度和趋势报表的 CSV/XLSX 导出。同步导出适合小到中等数据量，但如果筛选范围过大，直接生成文件会占用数据库、内存和请求线程，也会让前端下载体验不可控。真正的异步导出需要队列、任务状态和文件存储，本切片先补同步导出的安全边界。

## 范围

- 新增统一同步导出行数上限 `SYNC_EXPORT_ROW_LIMIT`，当前为 5000 行。
- 多行同步导出查询使用 `row_limit = SYNC_EXPORT_ROW_LIMIT + 1` 作为探测上限；如果返回行数超过同步上限，接口返回 `413 ADMIN_EXPORT_TOO_LARGE`。
- 覆盖订单明细导出、核销审计导出、核销失败审计导出、退款审计导出、产品维度导出和日报/小时/月度趋势导出。
- 支付对账导出是固定单行汇总，不走行数上限。

## 边界

- 本切片不实现异步任务、导出任务表、对象存储、后台任务轮询或下载链接过期。
- 超限响应仍使用统一失败壳：`success=false`、`code=ADMIN_EXPORT_TOO_LARGE`、`request_id`。
- 现有权限、CSRF、日期范围、筛选、DTO 防泄露、CSV/XLSX 公式注入防护和 XLSX XML 清洗不变。
- Repository 在有 `row_limit` 时使用参数绑定的 `LIMIT %s`，不把限制值拼进 SQL。

## 验收

- `backend/tests/test_admin_report_export_api.py` 覆盖报表导出超限、导出 filter 携带 `row_limit`、PostgreSQL 导出 SQL 使用参数化 `LIMIT %s`。
- `backend/tests/test_admin_check_in_api.py` 覆盖核销审计导出超限和参数化 `LIMIT %s`。
- `backend/tests/test_admin_refund_api.py` 覆盖退款审计导出超限和参数化 `LIMIT %s`。
- `scripts/verify-backend.sh` 作为提交前默认后端验收入口。
