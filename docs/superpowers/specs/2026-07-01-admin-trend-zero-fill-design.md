# 后台趋势报表补零设计

日期：2026-07-01

## 问题

后台日报、小时趋势和月度趋势已经能返回有订单活动的时间桶。前端图表在绘制连续时间轴时，如果缺少无订单日期、小时或月份，需要自己补零，容易造成页面之间口径不一致。

## 范围

- 给 `GET /api/admin/reports/daily-trend`、`GET /api/admin/reports/hourly-trend`、`GET /api/admin/reports/monthly-trend` 增加可选查询参数 `includeEmpty`。
- `includeEmpty` 默认 `false`，保持现有只返回有订单活动时间桶的行为。
- `includeEmpty=true` 时，后端按 `dateFrom` 到 `dateTo` 生成连续时间桶，并把缺失桶补成全 0 聚合行。
- 补零只发生在 service 层；repository 继续只查询真实聚合结果，避免 SQL 序列生成扩大数据库复杂度。

## 不做

- 不给产品维度报表、汇总报表或订单导出补零。
- 不做小时趋势 CSV/XLSX 导出。
- 不改变现有统计口径或金额聚合 SQL。
- 不实现前端页面。

## API

三个趋势接口新增查询参数：

- `includeEmpty?: boolean = false`

补零约束：

- `includeEmpty=true` 必须同时提供 `dateFrom` 和 `dateTo`。
- 日报补零最大 366 天。
- 小时补零最大 31 天。
- 月度补零最大 60 个月。

错误：

- `dateFrom > dateTo`：`422 ADMIN_REPORT_DATE_RANGE_INVALID`
- `includeEmpty=true` 但缺少边界日期：`422 ADMIN_REPORT_INCLUDE_EMPTY_RANGE_REQUIRED`
- 补零范围超过限制：`422 ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE`

## 安全边界

- 只补聚合 DTO，不新增个人信息、认证材料、内部 id 或 SQL 字段。
- 只读 GET 仍只要求管理员 session，不要求 CSRF。
- 补零前限制范围，避免一次请求生成过大的响应。
- 原始聚合查询仍使用参数绑定，日期不能拼进 SQL 字符串。

## 验收

- `backend/tests/test_admin_reports_api.py` 覆盖三类趋势补零、缺少日期边界、范围过大和默认行为不变。
- `backend/tests/test_openapi_contract.py` 覆盖 `includeEmpty` 查询参数。
- `docs/api-contract.md` 与 `docs/security-checklist.md` 记录补零边界。
- `scripts/verify-backend.sh` 和 `scripts/verify-integration.sh` 作为提交前门禁。
