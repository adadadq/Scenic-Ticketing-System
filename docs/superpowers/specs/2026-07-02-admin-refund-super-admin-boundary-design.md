# 管理员退款 SUPER_ADMIN 边界设计

日期：2026-07-02

## 问题

管理员账号已经有 `SUPER_ADMIN` 和 `OPERATOR` 角色，但退款写操作当前只校验管理员 session。退款会改变订单、支付、票项库存和审计日志，属于高风险资金状态变更，不能只依赖“已登录后台”这一层权限。

## 范围

- `POST /api/admin/orders/{order_no}/refund`
- `POST /api/admin/orders/{order_no}/refund/items`

## 决策

- 整单退款和部分退款必须由 `SUPER_ADMIN` 执行。
- `OPERATOR` 访问退款写操作返回 `403 ADMIN_FORBIDDEN`。
- 拒绝发生在调用订单退款 repository 之前，不能更新订单、支付、票项、库存或退款审计日志。
- 退款审计日志查询、CSV 导出和 XLSX 导出仍保持“任意管理员只读可访问”，不在本切片扩展完整权限矩阵。

## 安全边界

- 退款写操作仍必须通过 session-bound CSRF。
- 游客 session 仍返回 `403 ADMIN_FORBIDDEN`，匿名带 CSRF 仍返回 `401 ADMIN_AUTH_REQUIRED`。
- `OPERATOR` 拒绝时复用统一后台无权限错误，避免前端依赖过细的角色错误码。
- 审计日志只记录成功退款；权限拒绝不写业务退款审计日志。

## 验收

- `backend/tests/test_admin_refund_api.py::test_operator_cannot_refund_paid_order`
- `backend/tests/test_admin_refund_api.py::test_operator_cannot_partially_refund_selected_items`
- `backend/tests/test_admin_refund_api.py`
