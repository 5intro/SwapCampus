# SwapCampus — 校园闲置物品交易平台

北京林业大学 · 信息学院 《软件工程（课程设计）》T-02 选题项目

## 项目简介

面向北京林业大学师生的 C2C 校园闲置物品交易 Web 平台。提供商品发布与检索、站内实时通讯、面交确认、信用评价等核心功能，以提高校内资源流转率，为师生提供安全便捷的交易体验。

## 技术栈

| 层次 | 选型 |
|------|------|
| 后端 | Django 5 + Django REST Framework + Django Channels |
| 前端 | Vue 3 + Vite + Element Plus + Pinia |
| 数据库 | MySQL 8.0 |
| 实时通讯 | WebSocket（Channels + Redis） |
| 对象存储 | MinIO |
| 容器化 | Docker + Docker Compose |

## 快速开始

### 环境要求

- **Python 3.12+** (后端)
- **Node.js 18+** (前端)
- 数据库默认使用 **SQLite**（零配置），无需安装 MySQL 或 Redis

### 第一步：启动后端 (Django)

```bash
cd backend

# 1. 复制环境变量（首次）
cp .env.example .env

# 2. 创建虚拟环境（首次）
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 4. 安装依赖（首次）
pip install -r requirements/dev.txt

# 5. 数据库迁移（首次）
python manage.py migrate

# 6. 初始化种子数据（分类、标签）
python manage.py seed_products

# 7. 启动开发服务器
python manage.py runserver
```

> 后端默认运行在 **http://127.0.0.1:8000**
>
> Swagger API 文档: http://127.0.0.1:8000/api/docs/swagger/

打开**另一个终端**：

```bash
cd frontend

# 1. 安装依赖（首次，国内建议用镜像）
npm install --registry=https://registry.npmmirror.com

# 2. 启动开发服务器
npm run dev
```

> 前端默认运行在 **http://127.0.0.1:5173**
>
> Vite 自动将 `/api/*` 请求代理到后端 8000 端口

### 第三步：打开浏览器

访问 **http://127.0.0.1:5173**

### 测试账号

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 普通用户 | `20240001` | `test1234` | 测试学生账号 |
| 管理员 | `administer` | `123456` | 后台管理权限 |

> 创建更多测试账号：
> ```bash
> cd backend
> venv\Scripts\activate
> python manage.py shell -c "
> from apps.users.models import User
> User.objects.create_user(username='20240002', password='test1234', nickname='小明', campus='校本部')
> "
> ```
>
> 初始化/重置管理员账号：
> ```bash
> cd backend
> venv\Scripts\activate
> python manage.py seed_admin
> ```

### 需要注意

- 打开两个终端窗口，一个跑后端一个跑前端
- 后端终端保持 `runserver` 运行，**不要关闭**
- 前端的 Vite proxy 已经配好，`/api/*` 请求自动转发，无需手动配置跨域
- 默认使用 SQLite，数据库文件会生成在 `backend/db.sqlite3`，无需额外安装
- 管理员后台入口：登录管理员账号后，右上角用户菜单会出现"后台管理"选项

### 特色功能

- **学生证认证**：非管理员用户发布商品前需上传学生证照片，经管理员审核通过后方可使用发布功能，保障校园交易安全
- **消息撤回**：聊天消息发送后 3 分钟内可撤回，支持 WebSocket 实时同步和 REST 兜底

### 可选：Docker 一键部署

```bash
docker compose -f docker/docker-compose.yml up -d
```

### 目录结构速查

```
SwapCampus/
├── backend/          # Django 5 后端（API + WebSocket）
├── frontend/         # Vue 3 + Vite + Element Plus 前端
│   └── src/
│       ├── views/        # 13 个页面（含管理员后台 + 学生证认证）
│       ├── components/   # 9 个公共组件
│       ├── api/          # 7 个 API 模块（含 JWT 自动刷新 + 管理后台 + 认证审核）
│       ├── stores/       # 3 个 Pinia Store
│       ├── router/       # 路由 + 导航守卫（含管理员 + 认证路由守卫）
│       └── utils/        # 格式化 + 校验
├── docker/           # Docker 配置
└── docs/             # 课程设计文档
```

## 团队

4 人，前后端分层分工。详见 [CLAUDE.md](./CLAUDE.md)

## 课程信息

- **选题编号**：T-02
- **开发周期**：D1-D14（2周集中实习）
- **指导教师**：__________
