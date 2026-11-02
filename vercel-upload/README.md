# 讲稿工坊 · SlideScript

> 上传 PPT → 选一种演讲风格 → 拿到一份能直接照着念的逐页演讲稿。

前端 **Vue 3 + Vite**，后端 **FastAPI**，数据库 **MySQL 8**，大模型接任意 OpenAI 兼容接口（DeepSeek / 通义 / Moonshot / OpenAI）。没配大模型 Key 也能用——内置一套风格化模板引擎兜底。

![首页](docs/screenshots/home.png)

---

## ✨ 功能

- **PPT 解析**：逐页提取标题、要点、表格行与演讲者备注，页数与原件一致。
- **8 种演讲风格**：正式严谨 / 轻松幽默 / 激情鼓动 / 故事叙事 / 学术答辩 / 路演提案 / 温情致辞 / 极简干练。
- **按时长控字数**：1–30 分钟，按中文 240 字/分钟换算，自动分配到每一页，并给出单页建议用时。
- **逐页讲稿**：开场白 + 每页正文 + 结束语 + 现场提示，不是摘要，是口语。
- **在线改稿**：点开就能改，失焦自动保存。
- **演讲模式**：全屏提词器，方向键翻页、计时器、进度条、下一页预览。
- **导出**：Word（.docx）/ Markdown。
- **历史版本**：每次生成留存一版，可对比不同风格。

| 工作台 | 演讲模式 |
| --- | --- |
| ![工作台](docs/screenshots/workspace.png) | ![演讲模式](docs/screenshots/present.png) |

---

## 🚀 本地启动

### 1. 后端（FastAPI）

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # 按需修改
uvicorn app.main:app --reload --port 8000
```

> 也可以用仓库根目录的 `start-backend.cmd`（Windows 一键装依赖并启动）。

- 接口文档：<http://127.0.0.1:8000/api/docs>
- 健康检查：<http://127.0.0.1:8000/api/health>

**数据库**：首次启动会按 `.env` 里的 `MYSQL_URL` 探测 MySQL；连不上会自动回退到 `backend/data/app.db`（SQLite），只为了让你先跑起来。正式使用请配好 MySQL：

```sql
CREATE DATABASE ppt_speech DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```bash
mysql -uroot -p < backend/database/schema.sql
# 然后在 backend/.env 里设置：
# DATABASE_URL=mysql+pymysql://root:123456@127.0.0.1:3306/ppt_speech?charset=utf8mb4
```

表结构也会由 SQLAlchemy 在启动时自动创建（`Base.metadata.create_all`）。

### 2. 前端（Vue 3 + Vite）

```bash
cd frontend
pnpm install
pnpm dev          # http://127.0.0.1:5173
```

> Windows 一键：`start-frontend.cmd`。

Vite 已配置 `/api` 代理到 `http://127.0.0.1:8000`，无需额外跨域设置。

### 3. 体验

打开 <http://127.0.0.1:5173>，点「体验一下」或直接使用内置账号：

| 账号 | 密码 |
| --- | --- |
| `demo` | `demo123` |

体验账号自带一份示例 PPT《AI 时代，我们该如何学习》，可直接生成讲稿。

---

## 🤖 配置大模型（可选）

不配也能用，页面右上角会显示「模板引擎」；配好后显示「AI 生成」。

```ini
# backend/.env
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_MODEL=deepseek-chat
```

任何兼容 `/chat/completions` 的服务都行，例如：

| 服务 | LLM_BASE_URL | LLM_MODEL |
| --- | --- | --- |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| Moonshot | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |

调用失败或返回内容无法解析时，会自动降级到模板引擎，不会让页面报错。

---

## 🐳 Docker 一键起（MySQL + 后端 + 前端）

```bash
docker compose up --build
```

- 前端：<http://localhost:8080>
- 后端：<http://localhost:8000/api/docs>
- MySQL：`localhost:3306`，库名 `ppt_speech`，root 密码 `123456`

---

## 🗂 目录结构

```
ppt-speech/
├── backend/
│   ├── app/
│   │   ├── main.py              # 应用入口、CORS、启动时建表与示例数据
│   │   ├── config.py            # 环境变量配置
│   │   ├── database.py          # MySQL 优先 / SQLite 回退
│   │   ├── models.py            # ORM：users / presentations / slides / scripts
│   │   ├── schemas.py           # Pydantic 请求响应模型
│   │   ├── security.py          # PBKDF2 密码 + HMAC 令牌
│   │   ├── deps.py              # 当前用户依赖
│   │   ├── routers/             # auth / presentations / scripts / meta
│   │   └── services/
│   │       ├── ppt_parser.py    # python-pptx 解析
│   │       ├── generator.py     # 大模型 + 模板引擎
│   │       ├── styles.py        # 8 种风格定义
│   │       ├── exporter.py      # Word / Markdown 导出
│   │       └── sample_ppt.py    # 生成示例 PPT
│   ├── database/schema.sql      # MySQL 建表脚本
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── views/               # Landing / Login / Workspace / Present / History
│   │   ├── api.js               # 接口封装
│   │   ├── store.js             # 轻量全局状态
│   │   ├── router.js            # 路由与登录守卫
│   │   ├── App.vue
│   │   └── style.css
│   └── vite.config.js           # /api 代理
├── docs/
│   ├── 需求文档.md               # 需求规格说明书（课程用）
│   └── screenshots/
├── docker-compose.yml
└── start-backend.cmd / start-frontend.cmd
```

---

## 🔌 主要接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/login` | 登录，返回 Bearer 令牌 |
| POST | `/api/presentations/upload` | 上传 .pptx 并解析 |
| GET | `/api/presentations/{id}` | 文稿详情（含每页要点） |
| GET | `/api/styles` | 风格列表 |
| POST | `/api/scripts/generate` | 生成讲稿 |
| PATCH | `/api/scripts/{id}` | 修改讲稿 |
| GET | `/api/scripts/{id}/export?fmt=docx` | 导出 Word |

完整定义见 `docs/需求文档.md` 第 7 节或运行后的 `/api/docs`。

---

## 🌐 分享给别人看（临时公网链接）

本机跑的服务只有同一局域网能访问。要给老师/同学一个「点开就能看」的链接，可以用 SSH 反向隧道（无需安装任何客户端，Windows 自带 OpenSSH）：

```bash
# 前端打包后由后端统一提供（http://127.0.0.1:8000）
ssh -R 80:127.0.0.1:8000 nokey@localhost.run
```

终端会打印一个 `https://xxxx.lhr.life` 的地址，直接发给对方即可（对方任意网络都能打开）。

注意：

- 端口要写 `127.0.0.1` 而不是 `localhost`，否则可能先连 IPv6 而失败；
- 关掉终端 / 断网，链接立刻失效，重新运行会得到**新的**随机地址；
- 只想局域网内演示，用 `http://<你的IP>:8000` 即可，无需隧道。

---

## ☁️ 部署到 Vercel（免费公网链接）

项目已适配 Vercel Serverless：前端静态托管 + FastAPI 跑在 `api/index.py` 函数里，同一个域名，永久链接。

```bash
# 方式一：推到 GitHub，在 vercel.com/new 导入
# 方式二：本机 CLI 直接传
npm i -g vercel && vercel login && vercel --prod
```

完整步骤、环境变量、限制说明见 **[DEPLOY-VERCEL.md](DEPLOY-VERCEL.md)**。

> 注意 Vercel 的两条硬限制：上传文件 ≤ 4MB、数据存在 `/tmp`（实例重启会清空）。适合课程演示，长期使用建议走下面的 Docker 部署。

---

## ❓ 常见问题

**Q：上传 `.ppt` 报错？**
只支持 Office 2007 之后的 `.pptx`。用 PowerPoint 打开后「另存为 → PowerPoint 演示文稿 (.pptx)」。

**Q：生成的字数比目标时长短？**
模板引擎按目标字数扩写，但受每页要点数量限制，通常落在目标的 80–100%。配置大模型后字数控制会更准。页面会同时显示目标时长和实际字数，便于你现场调整。

**Q：`pnpm dev` 报 esbuild 相关错误？**
pnpm 10+ 默认不执行依赖的构建脚本。本仓库已在 `pnpm-workspace.yaml` 里允许 `esbuild`，若仍报错执行 `pnpm approve-builds` 并勾选 esbuild。另外 `.npmrc` 里设置了 `node-linker=hoisted` 与 `hoist-pattern[]=*`，确保 Windows 下依赖能正常解析。

**Q：没有 MySQL 会怎样？**
自动回退 SQLite（`backend/data/app.db`），功能完全一样，仅不适合多人并发。配好 MySQL 后重启即可切换，无需改代码。

---

## 📄 许可

课程作业 / 演示项目，可自由修改使用。
