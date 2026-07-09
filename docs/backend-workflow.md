# 后端执行工作流

本文档约束后端对话的日常执行方式。前端页面和样式由另一个对话负责；本对话只负责 Python 后端、数据库、API、安全和后端测试。

## 固定循环

每个后端切片都按以下顺序推进：

```text
读取事实源 -> 小步实现 -> 后端测试 -> 子代理审查 -> 修复审查问题 -> 复跑测试 -> 提交 -> 进入下一切片
```

## 事实源

每个切片至少读取：

- `docs/implementation-plan.md`
- `docs/api-contract.md`
- `docs/security-checklist.md`
- 与当前切片相关的后端源码和测试

当前后端测试会读取 `frontend/src/shared/api/types.ts`，对齐前端共享 API 类型与后端 DTO 字段。也会读取 `frontend/src/shared/api/client.ts` 和 `frontend/src/shared/api/endpoints.ts`，确认前端共享 API client 调用的 method/path/query key 存在于后端 OpenAPI，并检查 `apiRequest<T>()` 的前端返回类型与后端 OpenAPI `data` schema 是否一致。前端对 API 类型或共享请求入口做改动后，后端线程需要同步检查 `backend/tests/test_api_dto_contract.py` 和 `backend/tests/test_frontend_endpoint_contract.py` 的失败信息，而不是只看 Python 源码。

## 后端测试命令

默认测试命令：

```bash
.venv/bin/pytest backend/tests
```

联调前完整验收命令：

```bash
scripts/verify-integration.sh
```

该命令会运行后端闭环、后端全量测试、OpenAPI 导出、前端 lint 和前端 build。后端切片提交前仍默认使用 `scripts/verify-backend.sh`；影响前后端契约、OpenAPI、CSRF/Cookie、幂等键或共享 API client 的切片，优先使用 `scripts/verify-integration.sh`。浏览器 e2e smoke 需要显式开启：

```bash
VERIFY_INTEGRATION_E2E=1 scripts/verify-integration.sh
```

`VERIFY_INTEGRATION_E2E=1` 等价于 `mock`，用于前端 mock API 浏览器 smoke，不要求真实后端服务运行，并会忽略外部 `E2E_API_BASE_URL`。真实后端浏览器联调使用：

```bash
VERIFY_INTEGRATION_E2E=real scripts/verify-integration.sh
```

真实 API 默认地址为 `http://127.0.0.1:8000`，可通过 `E2E_API_BASE_URL` 覆盖。

若 `.venv` 不存在：

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
```

## 子代理审查

每完成一个切片，必须派子代理只读审查：

- 审查当前切片是否满足计划。
- 审查 API 响应契约是否一致。
- 审查安全清单相关项。
- 审查测试是否覆盖当前切片关键风险。

审查结果处理规则：

- Critical：必须立即修复，不进入下一切片。
- Important：原则上先修复再进入下一切片。
- Minor：可记录到后续，但不能影响安全和接口契约。

## 后端边界

本对话不主动修改：

- `frontend/`
- 前端页面设计稿
- React 组件
- 旧 `public/` 页面

如接口契约需要前端配合，只更新 `docs/api-contract.md` 或明确告知前端对话需要对齐。

## 提交规则

每个后端切片单独提交，提交前必须满足：

- 后端测试命令已 fresh run。
- 子代理审查已完成。
- 阻塞审查问题已修复。
- 不提交 `.venv`、`__pycache__`、`.pyc` 等本地运行产物。
