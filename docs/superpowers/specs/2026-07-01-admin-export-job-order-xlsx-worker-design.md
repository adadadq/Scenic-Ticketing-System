# 后台异步订单明细 XLSX 导出 worker 设计

## 背景

异步导出任务已经能创建、领取、生成订单 CSV 文件并通过受控下载端点取回。前端管理台在同一个任务流里也会提交 `ORDER_DETAIL + XLSX`，因此后端需要补齐 XLSX 生成能力，让 CSV/XLSX 两种订单明细格式都能完成从 `PENDING` 到 `SUCCEEDED` 的闭环。

## 范围

- 支持内部 worker 处理一条 `ORDER_DETAIL + XLSX` pending 任务。
- 复用同步订单 XLSX 导出的字段、手机号脱敏、公式注入防护和 XML 1.0 非法控制字符清洗。
- 复用现有 `AdminExportFileStorage`，由后端派生 `storage_key`，不接受客户端传入文件路径。
- 继续使用 `GET /api/admin/export-jobs/{job_id}/download` 下载生成后的 XLSX 文件。

## 不做

- 不新增常驻队列、并发 worker、对象存储、重试或清理策略。
- 不实现核销、退款、产品维度、趋势等其他异步导出类型。
- 不改变同步订单 XLSX 字段口径或 OpenAPI 文件下载响应格式。

## 安全边界

- worker 只从已经白名单归一化的 `filters.dateFrom/dateTo` 读取日期条件，并继续校验日期范围。
- XLSX 内容复用 `AdminReportService.to_orders_xlsx`，只包含订单级安全字段，不写完整手机号、证件号、session、CSRF、密码 hash、内部 id 或 SQL。
- 单元格继续写成 inline string，不生成公式节点；危险公式前缀和前导空格后的危险公式前缀必须加单引号。
- 文本写入前继续清理 XML 1.0 非法控制字符，避免脏数据损坏工作簿。
- 不支持的其他导出类型仍标记为 `FAILED + ADMIN_EXPORT_JOB_UNSUPPORTED`，不能无限停留在 `RUNNING`。

## 验收

- `ORDER_DETAIL + XLSX` pending 任务会生成 `.xlsx` 文件并标记 `SUCCEEDED`。
- 文件名使用 `admin-orders-<start>-<end>.xlsx`，存储 key 由后端派生。
- DTO 不返回内部 `storageKey`。
- `ORDER_DETAIL + CSV` 路径保持不变。
- `backend/tests/test_admin_export_jobs_api.py` 覆盖 XLSX 成功生成、CSV 不回归和未支持类型失败落库。
