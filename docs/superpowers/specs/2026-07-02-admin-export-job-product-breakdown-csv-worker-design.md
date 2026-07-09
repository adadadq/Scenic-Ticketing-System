# 后台异步产品维度报表 CSV 生成 worker 设计

日期：2026-07-02

## 问题

后台异步导出任务已经支持创建 `PRODUCT_BREAKDOWN` 任务，并对白名单 filters 做了日期校验和归一化；同步产品维度 CSV 导出也已经固定了产品/票种聚合字段、敏感字段边界和 CSV 公式注入防护。但内部 worker 暂未处理 `PRODUCT_BREAKDOWN + CSV`，任务会进入未支持失败分支，前端无法用异步任务流下载较大的产品维度报表。

## 范围

- 支持内部 worker 单次处理一条 `PRODUCT_BREAKDOWN + CSV` pending 任务。
- 复用同步产品维度 CSV 的字段、日期口径、聚合 DTO 和表格安全处理。
- 文件名继续使用 `admin-product-breakdown-<start>-<end>.csv`。
- `storage_key` 继续由后端按 `export-jobs/<jobId>/<fileName>` 派生，任务 DTO 不返回内部存储路径。
- `PRODUCT_BREAKDOWN + XLSX` 已由后续切片补齐；趋势报表异步 worker、常驻队列、重试、清理和生产对象存储不在本切片处理。

## 数据和安全边界

- worker 只读取任务中已归一化的 `dateFrom`、`dateTo`。
- 日期解析失败或日期倒挂继续落为 `FAILED + ADMIN_EXPORT_JOB_FILTERS_INVALID`。
- CSV 只包含产品维度聚合字段，不返回买家个人信息、支付流水号、渠道交易号、session、CSRF token、密码 hash、内部 id、SQL 或审计明细。
- CSV 单元格继续走统一表格转义，防护公式注入。
- 本切片完成时未支持的 XLSX 任务需要失败落库；后续 XLSX worker 已补齐后，未支持类型覆盖转移到趋势任务。

## 实现

- 在 `AdminReportService` 增加 `export_product_breakdown_csv_for_worker(date_from, date_to)`，不接收 `Request`，只复用日期校验、repository 聚合查询、DTO 转换和 `to_product_breakdown_csv`。
- 在 `AdminExportJobWorkerService.process_running_job` 增加 `PRODUCT_BREAKDOWN + CSV` 分支，解析日期 filters、调用报表服务、编码 UTF-8、写入受控存储并标记 `SUCCEEDED`。
- 不修改创建任务接口、下载接口、OpenAPI 请求 DTO 或前端契约。

## 验收

- `backend/tests/test_admin_export_jobs_api.py` 覆盖生成产品维度 CSV 文件、后端派生 `storage_key`、公开 DTO 不泄露 `storageKey` 和日期 filters 传递；未支持类型失败落库由后续 worker 切片继续覆盖。
- `docs/api-contract.md`、`docs/security-checklist.md`、`docs/backend-security-audit.md`、`docs/backend-milestone-status.md`、`docs/backend-acceptance-report.md` 和 `docs/decision-log.md` 同步记录支持矩阵和安全边界。
- 提交前运行聚焦测试、`scripts/verify-backend.sh`、`compileall` 和 `git diff --check`。
