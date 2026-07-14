# Windows 本地运行

本说明适用于从 GitHub 第一次拉取项目的组员。GitHub 只保存源码、数据库结构和演示数据，不包含任何人的 `.env`、本地数据库、数据库密码或真实业务数据。

## 1. 安装环境

安装以下软件：

- [Git for Windows](https://git-scm.com/downloads/win)
- 64 位 Python 3.12 或更高版本
- Node.js 22
- [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/)，使用 WSL 2 后端

在 PowerShell 中确认命令可用：

```powershell
git --version
py --version
node --version
npm --version
docker --version
```

## 2. 拉取代码

```powershell
git clone https://github.com/adadadq/Scenic-Ticketing-System.git
cd Scenic-Ticketing-System
```

## 3. 启动本地数据库

openGauss 5.0 以后在 Windows/macOS 的 Docker 环境中应使用 Lite 镜像。本项目的 Windows 本地开发使用 `enmotech/opengauss-lite:latest`；最终发布仍应在 Linux openGauss 6.0 环境完成兼容性验证。

先输入一个只用于自己电脑的数据库管理员密码，再启动容器：

```powershell
$GaussPassword = Read-Host "设置本地 openGauss 管理员密码"
docker volume create scenic-opengauss-data
docker run --name scenic-opengauss --privileged=true -d `
  -u root `
  -e "GS_PASSWORD=$GaussPassword" `
  -p 127.0.0.1:15432:5432 `
  -v scenic-opengauss-data:/var/lib/opengauss `
  enmotech/opengauss-lite:latest
docker logs scenic-opengauss
```

数据库文件保存在 Docker 数据卷 `scenic-opengauss-data` 中，不会写入 Git 仓库。端口只绑定到 `127.0.0.1`，不会直接开放给局域网。

### 初始化结构和运行账号

先复制 SQL 文件：

```powershell
docker cp .\database\schema.sql scenic-opengauss:/tmp/schema.sql
docker cp .\database\seed.sql scenic-opengauss:/tmp/seed.sql
docker exec -it scenic-opengauss bash
```

进入容器后运行：

```bash
su - omm
gsql -d postgres -p 5432
```

在 `gsql` 中执行下面的 SQL。把 `这里填写本机应用密码` 换成自己设置的强密码，并记住它；后面 `.env` 要使用同一个密码。

```sql
CREATE USER scenic_app WITH PASSWORD '这里填写本机应用密码';
CREATE DATABASE scenic_ticket;

\c scenic_ticket
\i /tmp/schema.sql
\i /tmp/seed.sql

REVOKE ALL ON DATABASE scenic_ticket FROM PUBLIC;
GRANT CONNECT ON DATABASE scenic_ticket TO scenic_app;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO scenic_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO scenic_app;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO scenic_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO scenic_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO scenic_app;

\q
```

退出容器：

```bash
exit
exit
```

这样数据库超级管理员 `omm` 只负责初始化和迁移，FastAPI 使用权限较低的 `scenic_app` 运行。网站中的游客和管理员则是 `visitor`、`admin_user` 表里的业务账号，不是数据库超级用户。

`schema.sql` 和 `seed.sql` 只在空数据库第一次初始化时执行。已有数据库升级应按照 [数据库迁移说明](../database/README.md) 执行迁移，不要重复导入种子数据。

## 4. 配置后端

在项目根目录复制环境变量模板：

```powershell
Copy-Item .env.example .env
notepad .env
```

至少检查以下配置，其中 `DB_PASSWORD` 填写刚才创建 `scenic_app` 时使用的密码：

```env
APP_ENV=development
DB_HOST=127.0.0.1
DB_PORT=15432
DB_NAME=scenic_ticket
DB_USER=scenic_app
DB_PASSWORD=这里填写本机应用密码
DB_SSLMODE=disable
```

`.env` 已被 `.gitignore` 排除，禁止使用 `git add -f .env` 上传。

创建虚拟环境、安装依赖并启动后端：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --env-file .env
```

后端默认地址是 `http://127.0.0.1:8000`。

新开一个 PowerShell 验证：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/health/db
```

## 5. 启动前端

再开一个 PowerShell：

```powershell
cd Scenic-Ticketing-System\frontend
npm ci
npm run dev
```

如果当前终端已经在项目根目录，则只需：

```powershell
cd frontend
npm ci
npm run dev
```

浏览器打开 `http://localhost:5173`。游客端可直接注册新的本地测试账号，具体操作见[系统使用说明](usage.md)。

## 6. 以后再次运行

数据库容器不需要重新创建：

```powershell
docker start scenic-opengauss
```

然后分别启动后端和前端：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --env-file .env
```

```powershell
cd frontend
npm run dev
```

停止数据库但保留数据：

```powershell
docker stop scenic-opengauss
```

查看数据库数据卷位置：

```powershell
docker volume inspect scenic-opengauss-data
```

## 7. 更新代码

```powershell
git pull origin main
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
cd frontend
npm ci
```

如果本次更新包含新的 `database/migrations/*.sql`，先备份数据库，再按照 [database/README.md](../database/README.md) 的顺序执行尚未应用的迁移。

## 常见问题

- `docker` 命令不可用：启动 Docker Desktop，确认 WSL 2 已安装并重启 Windows。
- 数据库容器启动失败：运行 `docker logs scenic-opengauss` 查看原因；密码必须满足 openGauss 的复杂度要求。
- `/api/health/db` 返回 503：核对 `.env` 中的端口、数据库名、用户名和应用密码。
- PowerShell 不允许激活虚拟环境：本说明直接调用 `.venv\Scripts\python.exe`，不需要修改执行策略。
- 前端能打开但请求失败：确认后端仍在运行，并且页面和 API 都使用 `localhost`，或都使用 `127.0.0.1`，不要混用 hostname。
