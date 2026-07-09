# 核销审计原因筛选设计

日期：2026-07-02

## 问题

撤销核销已经能把可选 `reason` 写入成功核销审计日志，并在列表、CSV、XLSX 中返回。但后台只能按票码、订单号、操作人和日期筛选，运营排查“误核销”“设备异常”等原因时仍要下载后手工筛选。

## 范围

- `GET /api/admin/check-in-logs`
- `GET /api/admin/check-in-logs.csv`
- `GET /api/admin/check-in-logs.xlsx`
- `CHECK_IN_AUDIT` 异步导出任务 filters

## 决策

- 新增可选查询参数 `reason`，查询参数最长 100 字，服务层 trim 后空字符串忽略；异步导出 filters 也按 100 字文本筛选边界校验。
- `reason` 使用大小写不敏感的模糊匹配，只匹配成功审计日志中的 `check_in_audit_log.reason`。
- CSV、XLSX 和异步 `CHECK_IN_AUDIT` worker 复用同一筛选语义。
- 异步导出公开 DTO 中 `reason` 视为敏感筛选值，返回 `***`；worker 内部仍使用完整值生成文件。

## 非目标

- 不强制撤销核销必须填写原因。
- 不给失败尝试审计增加原因字段。
- 不新增按原因聚合报表、风控规则、告警或审批流。

## 验收

- 核销审计检索可按 `reason` 过滤并分页。
- 核销审计 CSV/XLSX 导出可按 `reason` 过滤，且继续防护公式注入和敏感字段泄露。
- Postgres 查询对 `reason` 使用参数绑定，不拼接原始查询值。
- 异步导出任务允许 `CHECK_IN_AUDIT.filters.reason`，公开响应脱敏，worker 调用收到完整值。
