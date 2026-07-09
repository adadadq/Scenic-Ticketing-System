# 后台异步产品维度报表 XLSX 生成 worker 设计

日期：2026-07-02

## 问题

`PRODUCT_BREAKDOWN + CSV` 已经接入内部 worker，但运营人员常用 Excel 继续筛选、归档和转交产品维度报表。同步 XLSX 导出已经固定字段、日期口径和表格安全边界，异步 worker 只需要复用同一生成函数，不应新增统计口径或扩大数据面。

## 范围

- 支持内部 worker 单次处理一条 `PRODUCT_BREAKDOWN + XLSX` pending 任务。
- 复用同步产品维度 XLSX 的产品/票种聚合字段、日期校验、DTO 转换和表格安全处理。
- 文件名继续使用 `admin-product-breakdown-<start>-<end>.xlsx`。
- `storage_key` 继续由后端按 `export-jobs/<jobId>/<fileName>` 派生，任务 DTO 不返回内部存储路径。
- 趋势报表异步 worker、常驻队列、重试、清理和生产对象存储不在本切片处理。

## 数据和安全边界

- worker 只读取任务中已归一化的 `dateFrom`、`dateTo`。
- 日期解析失败或日期倒挂继续落为 `FAILED + ADMIN_EXPORT_JOB_FILTERS_INVALID`。
- XLSX 只包含产品维度聚合字段，不返回买家个人信息、支付流水号、渠道交易号、session、CSRF token、密码 hash、内部 id、SQL 或审计明细。
- XLSX 单元格继续写成 inline string，不生成公式节点，并清理 XML 1.0 非法控制字符。
- 未支持的趋势任务仍必须失败落库，不能停留在 `RUNNING`。

## 实现

- 在 `AdminReportService` 增加 `export_product_breakdown_xlsx_for_worker(date_from, date_to)`，不接收 `Request`，只复用日期校验、repository 聚合查询、DTO 转换和 `to_product_breakdown_xlsx`。
- 在 `AdminExportJobWorkerService.process_running_job` 增加 `PRODUCT_BREAKDOWN + XLSX` 分支，解析日期 filters、调用报表服务、写入受控存储并标记 `SUCCEEDED`。
- 不修改创建任务接口、下载接口、OpenAPI 请求 DTO 或前端契约。

## 验收

- `backend/tests/test_admin_export_jobs_api.py` 覆盖生成产品维度 XLSX 文件、后端派生 `storage_key`、公开 DTO 不泄露 `storageKey`、日期 filters 传递和未支持趋势任务失败落库。
- `docs/api-contract.md`、`docs/security-checklist.md`、`docs/backend-security-audit.md`、`docs/backend-milestone-status.md`、`docs/backend-acceptance-report.md` 和 `docs/decision-log.md` 同步记录支持矩阵和安全边界。
- 提交前运行聚焦测试、`scripts/verify-backend.sh`、`compileall` 和 `git diff --check`。
