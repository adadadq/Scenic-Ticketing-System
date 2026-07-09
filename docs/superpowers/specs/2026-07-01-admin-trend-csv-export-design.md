# 后台趋势报表 CSV 导出设计

## 问题

后台已经支持日报、小时和月度趋势 JSON，并支持 `includeEmpty=true` 返回连续时间桶。运营人员还需要把趋势数据下载到表格工具中留档或二次分析。本切片只做同步 CSV 导出，复用现有趋势查询、补零和管理员权限边界。

## 范围

- 新增 `GET /api/admin/reports/daily-trend.csv`。
- 新增 `GET /api/admin/reports/hourly-trend.csv`。
- 新增 `GET /api/admin/reports/monthly-trend.csv`。
- 三个端点都支持 `dateFrom`、`dateTo`、`includeEmpty`，语义与对应 JSON 趋势接口一致。
- CSV 列只包含趋势指标字段，不包含手机号、证件号、session、CSRF、密码 hash、内部 id、SQL 或审计字段。

## 非范围

- XLSX 导出。
- 异步导出、导出任务历史、对象存储或下载审计。
- 真实财务对账、支付渠道流水号或 BI 指标口径扩展。
- 前端页面按钮、下载交互或视觉验收。

## API 与 DTO

- `GET /api/admin/reports/daily-trend.csv` 返回 `text/csv; charset=utf-8`，文件名为 `admin-daily-trend-<start>-<end>.csv`。
- `GET /api/admin/reports/hourly-trend.csv` 返回 `text/csv; charset=utf-8`，文件名为 `admin-hourly-trend-<start>-<end>.csv`。
- `GET /api/admin/reports/monthly-trend.csv` 返回 `text/csv; charset=utf-8`，文件名为 `admin-monthly-trend-<start>-<end>.csv`。
- CSV 表头分别以 `reportDate`、`reportHour` 或 `reportMonth` 开头，后续字段与趋势 DTO 指标一致。

## 权限和安全

- 只允许管理员 session 访问；匿名返回 `ADMIN_AUTH_REQUIRED`，游客 session 返回 `ADMIN_FORBIDDEN`。
- GET 只读，不要求 CSRF header。
- 复用趋势日期校验：`dateFrom > dateTo` 返回 `ADMIN_REPORT_DATE_RANGE_INVALID`。
- 复用补零范围校验：`includeEmpty=true` 缺少日期边界返回 `ADMIN_REPORT_INCLUDE_EMPTY_RANGE_REQUIRED`，范围过大返回 `ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE`。
- CSV 单元格复用现有表格导出防护，危险公式前缀和前导空格后的危险公式前缀必须加单引号。

## 验收

- `backend/tests/test_admin_report_export_api.py` 覆盖三个趋势 CSV 下载、补零、管理员权限、错误码复用和公式注入防护。
- `backend/tests/test_openapi_contract.py` 覆盖三个 CSV 文件响应、`Content-Disposition` 响应头和 `includeEmpty` 查询参数。
- `scripts/verify-backend.sh` 作为后端全量门禁。
