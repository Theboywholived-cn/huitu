# 绘图系统（huitu）使用说明

一个基于 **Vue 3 + FastAPI + PostgreSQL** 的在线图表生成系统，支持模板化绘图、数据上传、参数配置、结果导出与后台模板管理。

## 1. 项目结构

- `frontend/`：前端（Vite + Vue 3）
- `backend/`：后端 API（FastAPI）
- `web/`：Nginx 配置与前端生产镜像
- `图像代码数据汇总/`：图表模板与样例数据
- `docker-compose.yml`：一键部署入口

## 2. Docker 一键部署（推荐）

### 2.1 环境准备

- Docker
- Docker Compose

### 2.2 拉取代码

```bash
git clone https://github.com/sushu0/huitu.git
cd huitu
```

### 2.3 检查模板目录挂载（重要）

`docker-compose.yml` 中 `backend` 的 `volumes` 需要能正确映射模板目录。

如果你不是原作者本机环境，建议改为相对路径：

```yaml
- "./图像代码数据汇总:/templates"
```

### 2.4 启动服务

```bash
docker compose up -d --build
```

### 2.5 打开系统

- 前端入口：[http://localhost:8080](http://localhost:8080)
- 健康检查：[http://localhost:8080/api/health](http://localhost:8080/api/health)

### 2.6 停止服务

```bash
docker compose down
```

## 3. 本地开发运行（不使用 Docker）

### 3.1 启动后端

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3.2 启动前端

```bash
cd frontend
npm install
npm run dev
```

开发模式默认访问地址：

- 前端：[http://localhost:5173](http://localhost:5173)
- 后端 API：[http://localhost:8000](http://localhost:8000)

## 4. 首次使用流程

1. 打开系统并登录。
2. 进入模板库，选择一个图表模板。
3. 先参考左侧“数据说明/样例文件”准备数据。
4. 上传 `.csv/.xlsx/.xls` 文件。
5. 调整图表样式参数后点击“生成图表”。
6. 预览并下载图片结果。

## 5. 默认账户与关键配置

默认管理员账户（可在 `docker-compose.yml` 或环境变量中修改）：

- 用户名：`admin`
- 密码：`admin123`

常用环境变量：

- `DATABASE_URL`：数据库连接
- `ADMIN_USERNAME` / `ADMIN_PASSWORD`：管理员账号
- `JWT_SECRET`：JWT 密钥
- `TEMPLATES_ROOT`：模板根目录（容器内通常为 `/templates`）

## 6. 常见问题

### 6.1 模板读取失败或看不到模板

请先检查：

- `backend` 服务是否启动成功
- `图像代码数据汇总` 是否正确挂载到容器 `/templates`
- `TEMPLATES_ROOT` 是否与挂载路径一致

### 6.2 三元图报错：`No module named 'ternary'`

说明运行环境缺少依赖，执行：

```bash
pip install python-ternary
```

或重新构建后端镜像：

```bash
docker compose up -d --build backend
```

### 6.3 页面显示 `Not Found`（新功能接口）

常见原因是前端已更新但后端仍是旧进程。可重建后端：

```bash
docker compose up -d --build backend
```

---

如果你准备部署到服务器，建议优先保证这三项：

- 模板目录挂载正确
- 后端镜像是最新构建
- 8080 端口可访问
