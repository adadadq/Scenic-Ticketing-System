# 后台异步导出 filters 脱敏

## 问题

异步导出任务需要保存完整 `filters` 供 worker 生成文件，但这些筛选条件可能包含票码、订单号和操作人用户名。如果管理员 API 在创建、列表、详情或重试响应中原样返回这些值，会扩大敏感运营查询条件的传播面。

## 范围

- 管理员 API 响应中的导出任务 `filters` 只保留字段结构。
- `ticketCode`、`orderNo`、`operatorUsername` 在公开响应中返回 `***`。
- `dateFrom`、`dateTo`、`failureCode`、`refundType`、`includeEmpty` 保持原值，方便前端显示任务筛选摘要。
- worker、仓库和文件生成流程继续使用完整 `filters`。

## 边界

- 不改变导出任务表结构。
- 不改变 `filters` 白名单、归一化、大小限制或错误码。
- 不改变 worker 对导出文件的筛选语义。

## 验收

- API 测试覆盖创建、列表和详情响应中的敏感 filter 值脱敏。
- API 测试覆盖 worker 内部领取任务仍能看到完整 `filters`。
- 后端完整验证脚本通过。
