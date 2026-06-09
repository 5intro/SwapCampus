# SwapCampus — Claude 项目操作准则

## 项目概述

SwapCampus 是北京林业大学校园闲置物品交易平台，为《软件工程（课程设计）》T-02 选题项目。面向全校师生提供 C2C 二手商品发布、检索、即时通讯、面交确认与信用评价服务。

- **选题编号**：T-02
- **团队规模**：4 人
- **开发周期**：D1-D14（集中实习 2 周）
- **仓库**：[5intro/SwapCampus](https://github.com/5intro/SwapCampus)

---

## 技术栈

| 层次 | 选型 | 说明 |
|------|------|------|
| 后端框架 | Django 5 + Django REST Framework | REST API、ORM、Admin、中间件 |
| 实时通讯 | Django Channels + Redis | WebSocket 异步通信 |
| 鉴权 | djangorestframework-simplejwt | JWT 无状态认证 |
| 前端框架 | Vue 3 + Vite | Composition API + 响应式设计 |
| UI 组件库 | Element Plus | 用户端 + 管理端组件 |
| 状态管理 | Pinia | Vue 3 官方推荐 |
| HTTP 客户端 | Axios | 拦截器 + 错误处理 |
| 数据库 | MySQL 8.0 | 团队均有使用经验，Django ORM 适配 |
| 对象存储 | MinIO | 本地 S3 兼容存储 |
| 容器化 | Docker + Docker Compose | 一键部署 |
| 测试 | pytest + pytest-django / Vitest | 单元测试覆盖率 ≥ 60% |
| 安全测试 | OWASP ZAP | Web 漏洞扫描 |
| 性能测试 | Locust / k6 | 压力测试 |

---

## 目录结构

```
SwapCampus/
├── backend/                        # Django 5 后端
│   ├── manage.py                   # Django 命令行入口
│   ├── pyproject.toml              # Ruff Lint + pytest + Coverage 配置
│   ├── config/                     # Django 项目配置
│   │   ├── settings.py             # 配置（分环境：dev/prod，通过 DJANGO_ENV 切换）
│   │   ├── urls.py                 # 根路由 + /api/docs/（Swagger/ReDoc）
│   │   ├── asgi.py                 # ASGI（HTTP + WebSocket 双协议）
│   │   ├── wsgi.py                 # WSGI
│   │   └── routing.py             # WebSocket 路由 → /ws/chat/<uuid>/
│   ├── apps/                       # 业务应用（按功能模块拆分）
│   │   ├── users/                  # M1 用户体系（✅ 后端A 已实现）
│   │   │   ├── apps.py             # AppConfig
│   │   │   ├── models.py           # User（AbstractUser 扩展）, CreditRecord
│   │   │   ├── serializers.py     # Register, User, UserProfile, CreditRecord
│   │   │   ├── views.py            # RegisterView, UserViewSet, JWT 包装视图
│   │   │   ├── urls.py             # API 路由（register|login|token/refresh|me|credit-records）
│   │   │   ├── services.py         # 信用分原子化变更（select_for_update + atomic）
│   │   │   ├── admin.py            # Django Admin 定制（User + CreditRecord）
│   │   │   └── tests/              # 18 个测试用例（注册/登录/个人信息/积分）
│   │   ├── products/               # M2 商品发布 + M3 检索（✅ 后端B 已实现）
│   │   │   ├── apps.py             # AppConfig
│   │   │   ├── urls.py             # API 路由
│   │   │   ├── models.py           # Product, Category, Tag, ProductImage
│   │   │   ├── serializers.py     # ProductList/Detail/Create/Update, Category, Tag, Image
│   │   │   ├── views.py            # ProductViewSet, CategoryViewSet, TagViewSet
│   │   │   ├── services.py         # 商品状态变更
│   │   │   ├── filters.py          # django-filter 高级筛选（分类/价格/成色/排序）
│   │   │   ├── admin.py            # ProductAdmin, CategoryAdmin, TagAdmin
│   │   │   └── tests/              # 26 个测试用例（CRUD/筛选/搜索/状态转换）
│   │   ├── transactions/           # M4 交易流程（✅ 后端B 已实现）
│   │   │   ├── apps.py             # AppConfig
│   │   │   ├── urls.py             # API 路由
│   │   │   ├── models.py           # Order, Review, FaceConfirm
│   │   │   ├── serializers.py     # OrderList/Detail/Create, Review, FaceConfirm
│   │   │   ├── views.py            # OrderViewSet, ReviewViewSet
│   │   │   ├── services.py         # 订单状态机（6状态 8+转换）、评价逻辑、面交确认
│   │   │   ├── admin.py            # OrderAdmin, ReviewAdmin, FaceConfirmAdmin
│   │   │   └── tests/              # 25 个测试用例（订单/状态机/面交/评价/积分联动）
│   │   ├── chat/                   # M5 站内通讯（✅ 后端A 已实现 + 消息撤回）
│   │   │   ├── apps.py             # AppConfig
│   │   │   ├── models.py           # Conversation, Message（含 is_recalled, recalled_at 撤回字段）
│   │   │   ├── consumers.py        # ChatConsumer（WebSocket 收发/已读/在线/撤回消息）
│   │   │   ├── serializers.py     # ConversationList/Detail/Create, Message（撤回内容转换）
│   │   │   ├── views.py            # ConversationViewSet（CRUD/消息/已读/撤回消息 3 分钟窗口）
│   │   │   ├── urls.py             # API 路由（conversations/.../messages|read|recall）
│   │   │   ├── admin.py            # Django Admin 定制
│   │   │   └── tests/              # 14 个测试用例（会话/消息/已读/权限）
│   │   └── admin_panel/            # M6 后台管理（✅ 后端B 已实现 + 管理 API 扩展）
│   │       ├── apps.py             # AppConfig
│   │       ├── urls.py             # Dashboard + Products + Reports + Users API 路由
│   │       ├── admin.py            # 跨模块 Admin 增强（Product/User/Order 批量操作 + CreditRecordInline）
│   │       ├── actions.py          # 批量操作实现（approve_products/hide_products/ban_users/cancel_orders_admin）
│   │       ├── views.py            # DashboardView + AdminProductListView + AdminReportListView + AdminUserListView
│   │       └── tests/              # 4 个测试用例（Dashboard/批量操作）
│   ├── core/                       # 共享基础设施
│   │   ├── models.py               # BaseModel（UUID pk, created_at, updated_at）
│   │   ├── pagination.py           # StandardPagination → 统一分页响应格式
│   │   ├── permissions.py          # IsOwnerOrReadOnly, IsOwner
│   │   ├── exceptions.py           # unified_exception_handler → 统一错误格式
│   │   ├── middleware.py           # JWTAuthMiddleware（WebSocket query_string JWT 鉴权）
│   │   └── utils.py                # 图片压缩、MD5 去重、响应构建辅助
│   ├── media/                      # 开发环境文件上传目录
│   ├── static/                     # Django 静态文件收集目录
│   └── requirements/               # Python 依赖
│       ├── base.txt                # Django 5 + DRF + Channels + SimpleJWT + MinIO
│       ├── dev.txt                 # pytest + ruff + factory-boy + django-extensions
│       └── prod.txt                # gunicorn + uvicorn + django-sslserver
│
├── frontend/                       # Vue 3 前端
│   ├── src/
│   │   ├── views/                  # 页面组件（按功能模块）
│   │   │   ├── HomeView.vue        # 首页（商品流+推荐）
│   │   │   ├── SearchView.vue      # 搜索与筛选
│   │   │   ├── ProductDetail.vue   # 商品详情
│   │   │   ├── PublishView.vue     # 发布商品
│   │   │   ├── ChatView.vue        # 聊天页面
│   │   │   ├── ChatList.vue        # 会话列表
│   │   │   ├── ProfileView.vue     # 个人主页
│   │   │   ├── MyProducts.vue      # 我的商品
│   │   │   ├── MyOrders.vue        # 我的订单
│   │   │   ├── LoginView.vue       # 登录
│   │   │   ├── RegisterView.vue    # 注册
│   │   │   └── AdminDashboardView.vue  # 管理员后台（数据看板/商品审核/举报处理/用户管理）
│   │   ├── components/             # 可复用组件
│   │   │   ├── layout/             # 布局组件（Navbar, Footer, Sidebar）
│   │   │   ├── product/            # 商品卡片、商品列表
│   │   │   ├── chat/               # 聊天框、消息气泡
│   │   │   ├── common/             # 通用组件（ImageUploader, Rating, Modal）
│   │   │   └── user/               # 用户相关（Avatar, CreditBadge）
│   │   ├── stores/                 # Pinia 状态管理
│   │   │   ├── auth.js             # 用户认证状态
│   │   │   ├── chat.js             # 聊天状态
│   │   │   └── products.js         # 商品列表缓存
│   │   ├── api/                    # API 请求层
│   │   │   ├── client.js           # Axios 实例（baseURL, 拦截器, JWT 刷新）
│   │   │   ├── auth.js             # 认证接口
│   │   │   ├── products.js         # 商品接口
│   │   │   ├── transactions.js     # 交易接口
│   │   │   ├── chat.js             # 聊天 REST 接口（含 recallMessage 撤回）
│   │   │   ├── users.js            # 用户接口
│   │   │   └── admin.js            # 管理后台接口（仪表盘/商品/举报/用户）
│   │   ├── router/
│   │   │   └── index.js            # Vue Router 路由配置
│   │   ├── utils/                  # 工具函数
│   │   │   ├── format.js           # 日期/价格格式化
│   │   │   └── validators.js       # 表单校验规则
│   │   ├── assets/                 # 静态资源（图标、全局样式）
│   │   ├── App.vue                 # 根组件
│   │   └── main.js                 # 入口文件
│   ├── public/                     # 不经过构建的静态资源
│   ├── index.html                  # HTML 模板
│   ├── vite.config.js              # Vite 配置（代理到 Django）
│   └── package.json
│
├── deploy.bat                       # Windows Server 一键部署脚本
├── .agents/skills/                  # taste-skill 设计框架（13 个 skill）
├── docker/                         # 容器化配置
│   ├── Dockerfile.backend          # Django 后端镜像
│   ├── Dockerfile.frontend         # Nginx + 前端构建产物
│   ├── docker-compose.yml          # 编排（Django + MySQL + Redis + MinIO + Nginx）
│   └── nginx.conf                  # Nginx 反向代理配置
│
├── docs/                           # 课程设计产出文档（D-01 ~ D-12）
│   ├── D-01_项目开题报告.docx
│   ├── D-02_需求规格说明书_SRS.docx
│   ├── D-03_概要设计说明书.docx
│   ├── D-04_详细设计说明书.docx
│   ├── D-05_数据库设计说明书.docx
│   ├── D-06_软件测试计划与测试报告.docx
│   ├── D-07_用户手册.docx
│   ├── D-08_部署与运维手册.docx
│   ├── D-09_课程设计总结报告.docx
│   ├── D-10_答辩PPT.pptx
│   ├── D-11_演示视频脚本.docx
│   └── D-12_项目源代码仓库/
│
├── memory/                         # Claude Code 项目记忆
├── .gitignore
├── CLAUDE.md                       # 本文件
└── README.md
```

---

## 前端 UI — 已实现（2026-06-06 更新）

> 前端已完整搭建。使用 **taste-skill**（Leonxlnx/taste-skill 28.5K stars）设计智能引擎辅助设计决策。
> 安装: `npm install && npm run dev`

### 设计系统

| Token | 值 | 来源 |
|-------|-----|------|
| 主色调 | `#43a047` 森林绿 | 北林校园主题 |
| 强调色 | `#e65100` 暖橙（价格） | taste-skill color calibration |
| 圆角 | 8px / 12px / 16px | CSS 变量 |
| 动效 | `cubic-bezier(0.16, 1, 0.3, 1)` 250-400ms | taste-skill motion preset |
| 字体 | 系统默认（PingFang SC） | 校园网性能优先 |
| 卡片阴影 | `0 4px 16px rgba(67,160,71,0.12)` 绿色调 | — |
| 反AI-Slop | 无紫蓝渐变、无 emoji 装饰、无 em-dash、无 Inter 字体 | taste-skill 规则 |

### App.vue 布局系统

App.vue 根据路由 `meta.layout` 自动渲染 Navbar 和 Footer：
- `layout: 'default'` → Navbar + 内容 + Footer
- `layout: 'blank'` → 仅内容（登录/注册页）
- `layout: 'chat'` → Navbar + 全高内容

### 已实现页面

| 页面 | 文件 | 状态 |
|------|------|------|
| 首页（商品流+分类+推荐） | `views/HomeView.vue` | ✅ |
| 搜索与筛选 | `views/SearchView.vue` | ✅ |
| 商品详情 | `views/ProductDetail.vue` | ✅ |
| 发布商品 | `views/PublishView.vue` | ✅ |
| 学生证认证 | `views/VerifyStudentView.vue` | ✅ |
| 聊天列表 | `views/ChatList.vue` | ✅ (10s 轮询) |
| 聊天对话 | `views/ChatView.vue` | ✅ (WebSocket + 轮询 + 撤回) |
| 个人主页（资料+商品+订单+积分+认证状态） | `views/ProfileView.vue` | ✅ |
| 我的商品 | `views/MyProducts.vue` | ✅ |
| 我的订单（完整状态机流程） | `views/MyOrders.vue` | ✅ |
| 登录 | `views/LoginView.vue` | ✅ |
| 注册 | `views/RegisterView.vue` | ✅ |
| 管理员后台（数据看板/商品审核/举报处理/用户管理/学生证审核） | `views/AdminDashboardView.vue` | ✅ |

### 已实现组件

| 组件 | 文件 |
|------|------|
| 导航栏（搜索+鉴权+消息徽标） | `components/layout/Navbar.vue` |
| 页脚 | `components/layout/Footer.vue` |
| 商品卡片（图片+价格+卖家+动效） | `components/product/ProductCard.vue` |
| 聊天框（消息列表+输入） | `components/chat/ChatBox.vue` |
| 消息气泡（自适应左右） | `components/chat/MessageBubble.vue` |
| 图片上传器 | `components/common/ImageUploader.vue` |
| 星级评分 | `components/common/Rating.vue` |
| 信用徽章 | `components/user/CreditBadge.vue` |

### 状态管理 (Pinia)

| Store | 说明 |
|-------|------|
| `stores/auth.js` | JWT 认证 + 自动刷新 + 用户信息 |
| `stores/chat.js` | 会话列表 + 未读计数 |
| `stores/products.js` | 商品列表 + 分类缓存 |

### API 层

所有 API 模块对应后端 `/api/` 路由：
`api/client.js` (Axios + JWT 拦截器 + 自动刷新) → `api/auth.js`, `api/products.js`, `api/transactions.js`, `api/chat.js`, `api/users.js`

### 关键实现细节

- **JWT 自动刷新**: 请求 401 → 用 refresh token 换新 access → 重试原请求
- **聊天**: WebSocket 主通道 + 8s REST 轮询兜底，断线 3s 自动重连
- **已读/未读**: 消息气泡显示已读/未读标签，打开会话自动标记已读并 WebSocket 实时同步给对方，Navbar 未读徽标 15s 轮询刷新
- **订单状态机**: 前端完整对应后端 6 状态：pending → accepted/rejected → face_confirm → completed
- **面交确认码**: 卖家生成 6 位码 → 买家输入验证 → 双方确认完成
- **信用积分**: CreditBadge 组件自动计算等级颜色（excellent/good/fair/poor）
- **图片上传**: Element Plus upload + multipart/form-data，自动压缩（后端处理）
- **路由守卫**: requiresAuth → /login, guest → / 自动跳转
- **响应式**: 所有页面适配移动端（布局流、隐藏部分导航元素）

---

## 团队分工（4 人 — 前后端分层）

| 角色 | 成员 | 职责范围 |
|------|------|---------|
| 后端 A | J0rthan | **users + chat**（M1+M5）JWT 认证、用户 CRUD、信用积分、Django Channels WebSocket、会话管理 |
| 后端 B | __xingyeyu______ | **products + transactions + admin_panel**（M2+M3+M4+M6）商品 CRUD、搜索 API、django-filter 筛选、订单状态机、评价、Django Admin 定制、数据看板 |
| 前端 A | Claude AI | **全部用户端页面 + 基础设施** 11 个页面、15 个组件、3个 Pinia Store、完整 API 层、路由守卫、WebSocket 聊天、响应式适配（taste-skill 辅助设计） |
| 前端 B | ________ | **代码审查 + 功能测试** 验证 API 对接、边界用例、移动端适配 |

### 备份机制
每个模块至少有一名备份人了解代码结构。后端 A↔B 互相备份核心 API 逻辑，前端 A↔B 互相备份页面组件。

---

## 开发工作流

### 分支策略
```
main          ← 保护分支，仅通过 PR 合并
├── dev       ← 日常开发集成分支
│   ├── feat/backend-users-chat   ← 后端 A：用户模块 + 聊天模块（M1+M5）
│   ├── feat/backend-products     ← 后端 B：商品模块 + 交易模块 + 管理面板（M2+M3+M4+M6）
│   ├── feat/frontend-home        ← 前端 A：首页+搜索
│   └── feat/frontend-profile     ← 前端 B：个人页+发布
└── release   ← D12 部署准备
```

### Commit 规范（Conventional Commits）
```
feat: 新增功能       feat(products): add product image upload API
fix: 修复 Bug        fix(chat): resolve WebSocket reconnect loop
docs: 文档更新       docs: update SRS section 3.2
refactor: 重构       refactor(users): extract credit calculation to service
test: 测试           test(transactions): add order state machine tests
chore: 杂项          chore: update docker-compose.yml
```

### PR 与 Code Review

1. 每个功能分支开发完成后，发起 PR 到 `dev`
2. **至少 1 名同伴 Review** 后才能合并（禁止 self-merge）
3. PR 标题遵循 Conventional Commits 格式
4. PR 描述须包含：做了什么、如何测试、关联的 Issue/文档
5. CI 通过（Lint + 测试）方可合并
6. 每日至少提交一次，杜绝"最后一天一次性合并"

### 每日站会（D6-D12 编码期）

- 时间：每天 9:00，≤ 15 分钟
- 每人回答：昨天做了什么、今天做什么、有无阻塞
- 阻塞问题当场协调或会后 30 分钟内解决

---

## API 与前后端协作规范

### 接口设计
- 所有 API 返回 JSON，遵循统一格式：
  ```json
  {
    "success": true,
    "data": { ... },
    "error": null,
    "pagination": { "page": 1, "page_size": 20, "total": 150 }
  }
  ```
- 错误响应：
  ```json
  {
    "success": false,
    "data": null,
    "error": { "code": "INVALID_CREDENTIALS", "message": "学号或密码错误" }
  }
  ```

### 接口文档
- DRF ViewSet 自动生成 OpenAPI 文档（drf-spectacular）
- 前端通过 `/api/docs/swagger/` 查看 Swagger UI，`/api/docs/redoc/` 查看 ReDoc
- D4-D5 设计阶段冻结 API 契约，双方确认后不得单方面修改
- 如需变更，先更新 API 文档，再同步修改前后端

### 环境变量
- `DJANGO_ENV`：环境切换（`dev` 默认 / `prod`）
- `DEBUG`：开发模式开关
- `DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT`：MySQL 连接
- `REDIS_URL`：Redis 连接（Channels Channel Layer）
- `MINIO_*`：MinIO 对象存储配置
- `USE_MINIO_STORAGE`：是否使用 MinIO 作为默认文件存储（默认 False，使用本地存储）

### 前端开发时 API Mock
- 开发初期后端 API 不可用时，前端使用 MSW (Mock Service Worker) 或 Vite proxy mock
- 文件放在 `frontend/src/api/mocks/`，不纳入生产构建

---

## 编码规范

### Python / Django

- 遵循 PEP 8，使用 Ruff 格式化与 Lint
- Django Model 字段显式声明 `related_name`
- ViewSet 的 `get_queryset()` 须做权限过滤（非管理员仅返回自己有权限的数据）
- 复杂业务逻辑抽离到 `services.py`，保持 View/ViewSet 轻量（≤ 30 行）
- 所有用户输入通过 DRF Serializer 校验，不信任客户端数据
- QuerySet 使用 `select_related` / `prefetch_related` 避免 N+1 查询

### JavaScript / Vue 3

- 使用 Composition API（`<script setup>`），不用 Options API
- 组件命名：PascalCase（`ProductCard.vue`），页面命名：`XxxView.vue`
- 每个组件文件 ≤ 300 行，超出则拆分子组件
- Pinia Store 只存放跨组件共享状态，页面私有状态用 `ref`/`reactive`
- API 调用统一通过 `api/` 目录下的模块，不在组件中直接写 `axios.get`
- 使用 ESLint + Prettier 保持代码风格一致

### 通用

- 命名：表意清晰 > 简短。`get_pending_orders_for_user()` > `get_orders()`
- 文件中不写"这段代码做什么"的注释；只写"为什么要这样做"的解释
- 不使用 `console.log` 提交；前端错误用统一 error handler
- Secret（密钥、Token、数据库密码）一律环境变量注入，不写进代码

---

## 后端架构决策（已实现）

### 主键策略
- 所有业务模型使用 **UUID 主键**（`core.models.BaseModel`），不在 API 中暴露自增 ID
- UUID 由应用层生成（`uuid.uuid4`），不依赖数据库

### 用户模型
- 自定义 `User` 扩展 `AbstractUser`，`username` 存储用户名（不再限制长度和格式）
- `credit_score` 初始 100 分，通过 `CreditRecord` 记录每次变更
- 信用等级按分数自动计算：`excellent(≥150)` / `good(≥100)` / `fair(≥60)` / `poor(<60)`
- **学生证认证**：`verification_status` 字段控制发布权限（unverified → pending → approved/rejected），非管理员用户必须上传学生证并通过审核后才能发布商品
- `student_id_card` 存储学生证照片，`verification_note` 记录管理员审核备注

### 信用分并发安全
- `services.add_credit_record()` 使用 `select_for_update` 行锁 + `@transaction.atomic`
- 积分下限为 0（不会变为负数）

### JWT 鉴权
- 登录/刷新 Token 的返回格式已包装为统一 API 格式
- WebSocket 鉴权：前端在连接 URL 的 query string 中传 `?token=<access_token>`
- `core.middleware.JWTAuthMiddleware` 异步验证 JWT 后注入 `scope["user"]`

### 会话去重
- 两名用户之间始终复用一个 `Conversation`（创建时自动查重）
- 同一对用户 + 不同商品不会创建重复会话

### 跨应用外键
- `chat.Conversation.product` 引用 `"products.Product"`（字符串延迟引用）
- `users.CreditRecord.related_order` 引用 `"transactions.Order"`（字符串延迟引用）
- 即使目标模型尚未创建，migrations 不会阻塞

### 消息排序
- 数据库层：`Message.Meta.ordering = ["created_at"]`（正序）
- API 层：REST 接口返回倒序（最新在前），WebSocket 推送按实际时间

---

## API 路由汇总（后端A 已实现）

### 用户体系（`/api/users/`）

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/register/` | 注册新用户 | 无 |
| POST | `/login/` | 登录获取 JWT | 无 |
| POST | `/token/refresh/` | 刷新 Access Token | 无 |
| GET | `/` | 用户列表（公开信息） | 可选 |
| GET | `/{id}/` | 用户详情（公开信息） | 可选 |
| GET | `/me/` | 当前用户完整信息 | JWT |
| PATCH | `/me/` | 更新当前用户信息 | JWT |
| POST | `/me/verify/` | 上传学生证（状态 → pending） | JWT |
| GET | `/me/verify/` | 查询认证状态 | JWT |
| GET | `/{id}/credit-records/` | 积分变更记录 | JWT |

### 站内通讯（`/api/chat/`）

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET | `/conversations/` | 我的会话列表 | JWT |
| POST | `/conversations/` | 创建/复用会话 | JWT |
| GET | `/conversations/{id}/` | 会话详情+最近消息 | JWT |
| GET | `/conversations/{id}/messages/` | 分页历史消息 | JWT |
| POST | `/conversations/{id}/messages/` | 发送消息（REST） | JWT |
| POST | `/conversations/{id}/read/` | 标记已读 | JWT |
| POST | `/conversations/{id}/messages/{msg_id}/recall/` | 撤回消息（3 分钟内） | JWT(发送者) |

### 商品模块（`/api/products/`）

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET | `/` | 商品列表（支持筛选 `?seller=&category=&status=&sort_by=`） | 可选 |
| POST | `/` | 发布商品 | JWT |
| GET | `/{id}/` | 商品详情 | 可选 |
| PATCH | `/{id}/` | 更新商品（含 status 下架） | JWT(卖家) |
| DELETE | `/{id}/` | 删除商品 | JWT(卖家) |
| GET | `/my/` | 我的商品 | JWT |
| GET | `/categories/` | 分类列表 | 无 |
| GET | `/tags/` | 标签列表 | 无 |

### WebSocket

| 路径 | 说明 | 鉴权 |
|------|------|------|
| `ws://host/ws/chat/{uuid}/?token=<jwt>` | 实时聊天 | query string JWT |

**WebSocket 消息类型：**

| type | 方向 | 说明 |
|------|------|------|
| `chat_message` | 客户端→服务端 | 发送消息 |
| `new_message` | 服务端→客户端 | 广播新消息 |
| `mark_read` | 客户端→服务端 | 按消息ID批量标记已读 |
| `read_conversation` | 客户端→服务端 | 标记整个会话已读（自动查找对方未读消息） |
| `messages_read` | 服务端→客户端 | 通知已读（携带 message_ids） |
| `typing` | 双向 | 输入状态 |
| `user_status` | 服务端→客户端 | 在线/离线状态 |
| `recall_message` | 客户端→服务端 | 撤回消息（3 分钟内） |
| `message_recalled` | 服务端→客户端 | 通知消息已被撤回 |

### 后台管理（`/api/admin/`）

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET | `/dashboard/` | 管理仪表盘（用户/商品/订单/举报统计） | JWT(staff) |
| GET | `/products/` | 商品列表（支持筛选、搜索、分页） | JWT(staff) |
| POST | `/products/{id}/{action}/` | 商品操作（approve/hide/delete） | JWT(staff) |
| GET | `/reports/` | 举报列表（支持状态筛选） | JWT(staff) |
| POST | `/reports/{id}/handle/` | 处理举报（resolve/dismiss） | JWT(staff) |
| GET | `/users/` | 用户列表（支持搜索、分页） | JWT(staff) |
| POST | `/users/{id}/manage/` | 管理用户（ban/unban） | JWT(staff) |
| GET | `/verifications/` | 学生证认证列表（支持状态筛选） | JWT(staff) |
| POST | `/verifications/{id}/review/` | 审核学生证（approve/reject） | JWT(staff) |

---

## 测试要求

### 覆盖率目标
- 后端：整体 ≥ 60%，核心交易域（transactions）≥ 80%
- 前端：关键组件和 Pinia Store 有测试覆盖

### 测试层次
| 层次 | 工具 | 覆盖内容 |
|------|------|---------|
| 单元测试 | pytest + pytest-django | Model 方法、Service 逻辑、Serializer 校验 |
| API 测试 | pytest + Django Test Client | ViewSet 接口、权限校验、错误码 |
| WebSocket 测试 | pytest + Channels Testing | Consumer 连接、消息收发 |
| 前端单元测试 | Vitest + Vue Test Utils | 组件渲染、Store 逻辑 |
| 集成测试 | pytest（后端）+ Playwright（前端 E2E） | 核心业务流程端到端 |
| 性能测试 | Locust | 关键 API RT/TPS/错误率 |
| 安全测试 | OWASP ZAP | OWASP Top 10 漏洞扫描 |

### 运行命令
```bash
# 后端测试
cd backend && pytest --cov=apps --cov-report=html

# 前端测试
cd frontend && npm run test:unit
```

---

## Git 仓库规则

### 提交频率
- D1-D5（文档阶段）：每完成一份文档提交一次
- D6-D12（编码阶段）：**每日至少 1 次提交**，鼓励小步提交
- 禁止"最后一晚全部 push"

### Commit 内容
- 一个 Commit 做一件事（功能/修复/重构分开）
- 不提交：`.env`、`node_modules/`、`__pycache__/`、`.DS_Store`、`media/uploads/`

### Tag 规范
- `kickoff` — D1 立项完成
- `req-v1.0` — D3 需求冻结
- `design-v1.0` — D5 设计冻结
- `dev-v1.0` — D9 编码完成
- `test-v1.0` — D11 测试完成
- `final-v1.0` — D14 答辩交付

---

## 文档管理

- 所有文档源文件放在 `docs/` 目录，与代码同仓库管理
- 文档更新与代码修改在同一 PR 中提交（"文档即代码"原则）
- 每份文档在 Git 中可追溯修改历史
- 命名格式：`<班级>_<组号>_<选题编号>_<文件简称>_v<版本号>.扩展名`

---

## AI 工具使用规范

### 允许的操作
- 使用 Claude Code / GitHub Copilot 辅助代码生成、文档起草、测试用例设计
- 使用 AI 进行代码解释、Bug 定位、重构建议
- 使用 AI 模拟干系人访谈（≤ 50% 访谈量）

### 禁止的操作
- 以 AI 全自动生成的代码作为核心实现（须有人工审查与理解）
- 隐瞒 AI 工具使用情况
- 直接拷贝 AI 生成的整段代码而不做理解与修改

### 申报要求
在《课程设计总结报告》附录中如实填写 AI 使用申报表。**如实申报不扣分**，隐瞒按学术不端处理。

---

## 环境搭建快速开始

### 前置要求
- Python 3.12+
- Node.js 18+
- Redis（Channels 依赖，开发可跳过，Docker 部署时自动提供）
- MySQL 8.0+（可选：生产/CI 使用；开发默认使用 SQLite 零配置启动）

### 数据库

**开发环境**：默认使用 SQLite（`backend/db.sqlite3`），零配置启动，无需安装 MySQL。

**切换到 MySQL**（生产/CI）：
```bash
# .env 中添加
DB_ENGINE=mysql
DB_NAME=swapcampus
DB_USER=swapcampus
DB_PASSWORD=your_password_here
DB_HOST=127.0.0.1
DB_PORT=3306
```
```sql
-- 仅在需要 MySQL 时执行一次
CREATE DATABASE swapcampus CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'swapcampus'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON swapcampus.* TO 'swapcampus'@'localhost';
FLUSH PRIVILEGES;
```

> 注意：`mysqlclient` 在 macOS + MySQL 9.x 下存在链接兼容性问题，项目使用纯 Python 的 **PyMySQL** 作为 MySQL 驱动（`manage.py` 中自动注册 `pymysql.install_as_MySQLdb()`）。

### 本地开发
```bash
# 1. 克隆仓库
git clone git@github.com:5intro/SwapCampus.git
cd SwapCampus

# 2. 后端
cd backend
cp .env.example .env                 # 复制环境变量模版（默认 SQLite，无需修改）
python -m venv venv
source venv/bin/activate             # Windows: venv\Scripts\activate
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py seed_products          # 初始化分类和标签数据
python manage.py runserver           # 开发用 WSGI；如需 WebSocket 功能使用 Daphne/uvicorn

# 3. 前端
cd frontend
npm install
npm run dev

# 4. 运行测试
cd backend && pytest --cov=apps --cov-report=html   # 30 个测试，目标覆盖率 ≥ 80%
cd frontend && npm run test:unit                     # 前端测试

# 5. 代码质量
ruff check .      # Lint 检查
ruff format .     # 自动格式化

# 6. 完整部署（Docker）
docker compose -f docker/docker-compose.yml up -d
```

### Windows Server 直接部署

> 阿里云 ECS 不支持嵌套虚拟化，生产环境使用 Waitress（Windows 兼容的 WSGI 服务器）代替 gunicorn。

```batch
:: 将项目文件复制到 C:\SwapCampus\
:: 确保 .env 放在 C:\SwapCampus\ （与 deploy.bat 同目录）
cd C:\SwapCampus
deploy.bat
```

部署后 Nginx 指向 `C:\SwapCampus\frontend\dist` 提供前端，反向代理 `/api/` 到 `127.0.0.1:8000`。

### 部署更新（仅替换修改的文件夹）

```powershell
# 前端：替换 src/ 和 public/ 后
cd C:\SwapCampus\frontend
npm run build

# 后端：替换 apps/ 和 core/ 后重启
Ctrl+C
venv\Scripts\activate
waitress-serve --port=8000 config.wsgi:application
```

---

## 课程关键节点

| 阶段 | 日期 | 关键动作 | 交付物 |
|------|------|---------|--------|
| 立项 | D1 | 选题+组队+开题答辩 | D-01, T-01, T-02 |
| 需求 | D2-D3 | 需求调研+建模+评审 | D-02 |
| 设计 | D4-D5 | 概要+详细+数据库设计 | D-03, D-04, D-05 |
| 编码 | D6-D9 | 分模块开发+每日PR | 可运行系统+测试 |
| 测试 | D10-D11 | 集成+性能+安全测试 | D-06 |
| 部署 | D12 | 容器化+用户手册 | D-07, D-08 |
| 验收 | D13-D14 | 答辩+归档 | D-09, D-10, D-11, T-04, T-05 |

---

## 更新日志

### 2026-06-09 — 学生证上传 URL 修复

**问题**：学生证上传时前端显示「网络错误」，上传请求失败。

**根因**：后端 `UserViewSet` 中 `verify` action 未指定 `url_path`，DRF SimpleRouter 将其路由为 `POST /api/users/verify/`，而前端调用的是 `POST /api/users/me/verify/`。URL 不匹配导致 Django 返回 404 HTML 页面，axios 拦截器解析不到 `response.data.detail` 字段，回退显示泛化的「网络错误」提示。

**修复**：`backend/apps/users/views.py` 第 169 行，`@action(detail=False, methods=["post"], ...)` → `@action(detail=False, methods=["post"], url_path="me/verify", ...)`，使后端 URL 与前端调用路径一致。`@verify.mapping.get` 会自动继承同一 `url_path`，因此 GET 查询认证状态也同步修复为 `/api/users/me/verify/`。

### 2026-06-09 — 学生证认证 + 用户名限制移除

**用户名限制移除**
- 后端 `RegisterSerializer` 不再限制 username 为 8-9 位数字（移除 `validate_username` 正则校验和 `min_length`/`max_length` 约束）
- 前端 `validators.js` 的 `studentIdRule` 移除 pattern 正则，仅保留非空校验
- 前端 `RegisterView.vue` 移除 `maxlength="9"`，标签由"学号"改为"用户名"

**学生证认证审核**
- 后端 `User` 模型新增 `verification_status`（unverified/pending/approved/rejected）、`student_id_card`（ImageField）、`verification_note` 字段
- 后端 `UserProfileSerializer` 新增 `verification_status`、`student_id_card`、`verification_note` 字段
- 后端新增 `StudentIdCardUploadSerializer` 用于上传学生证
- 后端 `UserViewSet` 新增 `verify` action：POST 上传学生证（状态 → pending）、GET 查询认证状态
- 后端 `AdminVerificationListView`：GET 待审核列表 + POST 通过/拒绝（附备注）
- 后端 `ProductViewSet.create` 新增认证检查：非管理员且未通过认证 → 返回 403
- 前端新增 `VerifyStudentView.vue`：学生证上传页面，展示认证状态（未认证/审核中/已通过/已拒绝）
- 前端 `router/index.js` 新增 `/verify-student` 路由 + `/publish` 路由增加 `requiresVerification` meta + 路由守卫检查
- 前端 `AdminDashboardView.vue` 新增"学生证审核"Tab（列表 + 通过/拒绝操作）
- 前端 `ProfileView.vue` 新增认证状态标签展示
- 前端 `api/users.js` 新增 `uploadStudentIdCard` 和 `getVerificationStatus`
- 前端 `api/admin.js` 新增 `getVerifications` 和 `reviewVerification`

### 2026-06-09 — 管理员角色 + 消息撤回

**管理员角色**
- 新增 `python manage.py seed_admin` 命令，创建默认管理员账号：`administer` / `123456`
- 后端 `UserProfileSerializer` 新增 `is_staff` 字段，前端可据此判断管理员身份
- 后端 `admin_panel/views.py` 新增 `AdminProductListView`（商品审核/隐藏/删除）、`AdminReportListView`（举报处理/驳回）、`AdminUserListView`（用户封禁/解封）
- 后端 `admin_panel/urls.py` 新增对应 API 路由
- 前端新增 `views/AdminDashboardView.vue`：数据看板（4 个统计卡片 + 最近注册用户）、商品管理（搜索/筛选/审核/隐藏/删除）、举报处理（待处理/已处理/驳回列表）、用户管理（搜索/封禁/解封）
- 前端新增 `api/admin.js`：仪表盘、商品、举报、用户的完整 API 调用模块
- 前端 `router/index.js` 新增 `/admin` 路由 + `requiresAdmin` 守卫（仅 `is_staff` 用户可访问）
- 前端 `Navbar.vue` 用户菜单新增"后台管理"入口（仅管理员可见）

**消息撤回**
- `Message` 模型新增 `is_recalled`（BooleanField）和 `recalled_at`（DateTimeField），创建迁移 `chat/0003`
- `MessageSerializer` 的 `content` 改为 `SerializerMethodField`：已撤回消息返回"该消息已被撤回"
- `ConversationViewSet` 新增 `recall_message` action：验证发送者权限 + 3 分钟时间窗口
- `ChatConsumer` 新增 `recall_message` WebSocket 消息类型 + `message_recalled` 事件广播
- 前端 `MessageBubble.vue`：自己消息 3 分钟内显示"撤回"按钮，已撤回消息灰色虚线样式
- 前端 `ChatView.vue` 处理 `handleRecallMessage`（优先 WebSocket，REST 兜底）和 `message_recalled` WebSocket 事件
- 前端 `api/chat.js` 新增 `recallMessage` API 函数

### 2026-06-06 — Bug 修复与完善

**种子数据**
- 新增 `python manage.py seed_products` 命令，初始化 7 大类 + 20 子类的二级分类体系，5 个标签（去除了跟成色重复的"几乎全新""九成新""八成新""功能正常""有瑕疵"）
- 文件：`apps/products/management/commands/seed_products.py`

**订单筛选修复**（`apps/transactions/views.py`）
- `OrderViewSet.get_queryset()` 新增 `status` 查询参数过滤，支持逗号分隔多状态。修复了全部/待确认/进行中/已完成 Tab 切换无效的问题。

**取消/拒绝原因**（`apps/transactions/views.py`、`serializers.py`、`frontend/src/views/MyOrders.vue`）
- 后端 `cancel`/`reject` action 统一读取 `reason` 参数，`OrderListSerializer` 新增 `cancel_reason` 和 `cancel_by` 字段
- 前端订单卡片新增红色提示条展示取消人 + 原因

**消息气泡布局**（`frontend/src/components/chat/MessageBubble.vue`）
- 修正为：对方 `[头像][消息]`，自己 `[消息][头像]`

**离开聊天弹"未找到"**（`frontend/src/views/ChatView.vue`）
- WebSocket close 的 `setTimeout` 未清除导致 3 秒后发无效请求 → 404。新增 `reconnectTimer` 并在 `onUnmounted` 中 clearTimeout

**面交确认码**（`frontend/src/api/transactions.js`、`frontend/src/views/MyOrders.vue`）
- 修正 API 路径：`generateConfirmCode` 改用 `GET .../face_confirm/`，`verifyConfirmCode` 改用 `POST .../face_confirm/`
- 确认码生成后持久显示在订单卡片上（绿色大号字体、可选中复制），支持页面刷新后自动恢复、卖家可重新生成

**商品状态标签**（`frontend/src/components/product/ProductCard.vue`）
- 非 active 状态之前统一显示"已售出"，修正为按实际状态区分：sold→已售出、hidden→已下架、reserved→已预定

---

> 本文件是项目的操作准则，所有 AI 辅助操作、团队协作、代码提交均以此为准。
> 如有与课程任务书冲突之处，以课程任务书为准。
