# 后台异步导出存储 provider 边界

## 问题

后台异步导出当前使用本地文件目录保存 CSV/XLSX。后续如果接 S3、OSS 或 COS，不能让部署人员只改环境变量就误以为生产对象存储已经可用；在真正接入云存储前，后端需要先明确当前 provider 契约和防误配边界。

## 范围

- 新增 `ADMIN_EXPORT_STORAGE_PROVIDER` 配置，默认值为 `local`。
- 配置值会 trim 并转小写。
- 当前只支持 `local`，任何未知 provider 都在配置校验阶段拒绝启动。
- API、单次 worker、循环 worker 和清理脚本统一通过 `get_admin_export_file_storage()` 获取存储实现。

## 边界

- 不接入 S3、OSS、COS 或任何云厂商 SDK。
- 不改变现有 `storage_key`、下载接口、清理逻辑或任务状态机。
- 不新增前端字段；前端继续只看到任务状态和下载接口。

## 安全要点

- 未实现的 provider 不能静默回退到本地存储。
- `storage_key` 仍只在服务端内部使用，不进入公开 DTO。
- 本地 provider 继续限制在 `ADMIN_EXPORT_STORAGE_DIR` 内，拒绝路径穿越。

## 验收

- 配置测试覆盖默认 `local`、大小写归一化和未知 provider 拒绝。
- 脚本测试覆盖单次 worker、循环 worker 和清理脚本都走统一 storage factory。
- 后端完整验证脚本通过。
