# 后台趋势报表 XLSX 导出设计

## 问题

后台趋势 JSON 和 CSV 导出已经覆盖日报、小时和月度趋势。运营人员常用 Excel 做留档、筛选和截图汇报，因此需要在不扩大数据面的前提下提供同步 XLSX 下载。

## 范围

- 新增 `GET /api/admin/reports/daily-trend.xlsx`。
- 新增 `GET /api/admin/reports/hourly-trend.xlsx`。
- 新增 `GET /api/admin/reports/monthly-trend.xlsx`。
- 三个端点都支持 `dateFrom`、`dateTo`、`includeEmpty`，语义与对应 JSON 趋势接口一致。
- XLSX 字段与趋势 CSV 完全一致，只包含趋势聚合指标。

## 非范围

- 异步导出、导出历史、对象存储或下载审计。
- 真实财务对账、支付渠道流水号或 BI 指标口径扩展。
- 前端页面按钮、下载交互或视觉验收。

## API 与文件响应

- 成功响应为 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`。
- 文件名为 `admin-daily-trend-<start>-<end>.xlsx`、`admin-hourly-trend-<start>-<end>.xlsx` 或 `admin-monthly-trend-<start>-<end>.xlsx`。
- 工作表只使用 inline string 单元格，不生成公式节点。

## 权限和安全

- 只允许管理员 session 访问；匿名返回 `ADMIN_AUTH_REQUIRED`，游客 session 返回 `ADMIN_FORBIDDEN`。
- GET 只读，不要求 CSRF header。
- 复用趋势日期校验和补零范围校验。
- XLSX 复用现有表格安全函数，危险公式前缀和前导空格后的危险公式前缀必须加单引号。
- 写入 XML 前清理 XML 1.0 非法控制字符，避免脏文本破坏 workbook。
- 不导出完整手机号、证件号、session、CSRF、密码 hash、内部 id、SQL 或审计字段。

## 验收

- `backend/tests/test_admin_report_export_api.py` 覆盖三个趋势 XLSX 下载、补零、管理员权限、错误码复用、敏感字段防泄露、无公式节点和 XML 1.0 清洗复用。
- `backend/tests/test_openapi_contract.py` 覆盖三个 XLSX 文件响应、`Content-Disposition` 响应头和 `includeEmpty` 查询参数。
- `scripts/verify-backend.sh` 作为后端全量门禁。
