# 后台异步导出 worker 脚本输出脱敏

## 问题

后台异步导出公开 API 已经对 `ticketCode`、`orderNo`、`operatorUsername` 这类敏感筛选值脱敏，但 `scripts/process-admin-export-job.py` 和 `scripts/run-admin-export-worker.py` 仍会把 worker 返回的任务 DTO 直接写到 stdout。部署后 stdout 往往进入终端、CI 或 systemd journal，如果脚本输出完整 `filters`，会扩大运营查询条件的传播面。

## 范围

- 单次 worker 脚本 `scripts/process-admin-export-job.py` 的 `job` 输出必须复用公开 DTO 的 filters 脱敏规则。
- 循环 worker 脚本 `scripts/run-admin-export-worker.py` 的 `lastJob` 输出必须复用公开 DTO 的 filters 脱敏规则。
- 日期、枚举和布尔筛选仍保留原值，便于运维判断任务口径。
- worker 内部处理任务时仍使用完整 `filters`，不能把脱敏值传回文件生成流程。

## 边界

- 不修改数据库记录、worker 状态机、文件生成、下载端点或公开 API 行为。
- 不改变脚本错误 JSON 的固定脱敏输出。
- 不新增真实队列、真实对象存储或日志系统集成。

## 验收

- `backend/tests/test_openapi_export_script.py` 覆盖单次 worker 脚本和循环 worker 脚本输出脱敏。
- `scripts/verify-backend.sh` 通过。
