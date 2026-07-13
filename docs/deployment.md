# 部署与回滚

## 生产结构

推荐使用版本目录加 `current` 软链接：

```text
/opt/scenic-ticket/releases/<release-id>/
/opt/scenic-ticket/current -> releases/<release-id>
/opt/scenic-ticket/backups/<release-id>/
/etc/scenic-ticket/backend.env
```

Nginx 提供 `frontend/dist`，并把 `/api/` 反向代理到 `127.0.0.1:8000`；FastAPI 由 systemd 管理；openGauss 可独立运行或由容器托管。

## 发布步骤

1. 本地运行后端测试、前端 lint、契约检查和生产构建。
2. 在服务器备份当前数据库、环境文件和当前版本路径。
3. 上传源码到新的只读版本目录，不覆盖旧版本。
4. 在新版本创建 `.venv` 并安装 `backend/requirements.txt` 的锁定版本。
5. 按顺序执行尚未应用的数据库迁移。
6. 原子切换 `current` 软链接并重启 FastAPI。
7. 检查 Nginx、FastAPI、数据库和关键业务链路。
8. 确认无 500、异常堆栈和 Nginx error log 后再结束维护窗口。

## 最低验收

```bash
curl -f http://127.0.0.1:8000/api/health
curl -f http://127.0.0.1:8000/api/health/db
curl -f http://your-domain.example/
curl -f http://your-domain.example/api/health/db
```

还必须实际验证：

- 游客注册/登录、票种和时段读取。
- 常用出行人新增、编辑、删除。
- 创建订单、模拟支付、查看票码、游客退款。
- 管理员登录、系统设置读写、票种读写。
- 数据库退款审计操作人约束。
- 393 × 852 下购票、订单和游客服务无横向溢出。

## 回滚

1. 停止或限制新的写请求。
2. 把 `current` 软链接切回上一个版本。
3. 若迁移不向后兼容，按发布前备份恢复数据库。
4. 重启 FastAPI，检查 `/api/health`、`/api/health/db` 和日志。
5. 重新验证登录、下单与后台读写。

不要只回滚代码而保留不兼容的数据库结构，也不要在没有备份的情况下执行破坏性迁移。
