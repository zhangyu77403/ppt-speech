# 部署到 Vercel 指南

本项目已改造成 Vercel 可部署的形态：**Vue 前端静态托管 + FastAPI 跑在 `api/` 下的 Serverless Function 里**，同一个域名，不需要服务器、不需要 Nginx。

> 部署成功后地址形如 `https://xxx.vercel.app`，永久有效，可直接发给老师。

---

## 0. 目录结构（部署版）

```
ppt-speech/
├── api/                      ← Vercel 函数目录
│   ├── index.py              ← 入口：导出 FastAPI 的 app
│   ├── requirements.txt      ← 函数依赖（Vercel 自动 pip install）
│   └── app/                  ← 后端代码副本（由 backend/app 同步而来）
├── backend/                  ← 本地开发 / Docker 用的后端原始代码
├── frontend/                 ← Vue 3 + Vite 前端
├── vercel.json               ← 构建与路由配置
├── package.json              ← 提供 build 脚本
└── requirements.txt
```

> `api/app/` 是 `backend/app/` 的**部署副本**——Vercel 只把 `api/` 目录打进函数包。
> 改了后端代码后运行一次 `python scripts/sync_api_backend.py` 重新同步（打包时会自动做）。

**对 Vercel 的适配（已写进代码）**

| 项目 | 本地 | Vercel |
| --- | --- | --- |
| 数据目录 | `backend/data/` | `/tmp/ppt-speech` |
| 数据库 | MySQL → 无则 SQLite | SQLite（`/tmp`） |
| 上传上限 | 30MB | 4MB（Vercel 请求体上限 4.5MB） |
| 大模型超时 | 180s | 50s（函数上限 60s） |
| 端口/进程 | uvicorn | `api/index.py` 导出 `app` |

---

## 1. 前置

- Vercel 账号（GitHub 注册即可，免费）
- 代码在 GitHub（方式一），或者装 Node.js 用 CLI（方式二），或者直接网页拖拽（方式三）

---

## 2. 方式一：GitHub 导入（最稳）

```bash
git init
git add .
git commit -m "讲稿工坊"
git branch -M main
git remote add origin https://github.com/你的用户名/ppt-speech.git
git push -u origin main
```

然后打开 <https://vercel.com/new> → 选仓库 → **Framework Preset 选 `Other`** → Deploy。
构建命令与输出目录由 `vercel.json` 提供，不用手填。

`.gitignore` 已排除 `node_modules`、`backend/_deps`、`backend/data`、`.env`。

---

## 3. 环境变量

项目 → Settings → Environment Variables：

| 变量名 | 必填 | 说明 |
| --- | --- | --- |
| `SECRET_KEY` | ✅ | 任意 32 位随机字符串，登录令牌签名用 |
| `LLM_API_KEY` | ⭕ | 不填则用内置模板引擎，功能仍完整 |
| `LLM_BASE_URL` | ⭕ | 默认 `https://api.deepseek.com/v1` |
| `LLM_MODEL` | ⭕ | 默认 `deepseek-chat` |

**不要**填 `DATABASE_URL` / `MYSQL_URL`——Vercel 上没有本地 MySQL。

---

## 4. 方式二：CLI（不折腾网页）

```bash
npm i -g vercel
cd ppt-speech
vercel login
vercel --prod
```

首次会问几个问题，一路回车用默认值即可（CLI 会读取 `vercel.json`）。

---

## 5. 方式三：网页拖拽

1. 解压 `ppt-speech-vercel.zip`，得到 **`ppt-speech` 文件夹**
2. 把这个**文件夹本身**拖到 <https://vercel.com/new/drop>
3. 正确时应显示 **约 80 个文件、2MB 左右**

**判断标准**：文件数是几十个，不是几千个。如果显示几百 MB，说明拖成了上一级目录（把 `node_modules` 也带上了），立刻取消。

**如果提示 "configured as Vite"**：项目 → Settings → Build & Development Settings：
Framework Preset 选 `Other`，Build Command / Output Directory / Install Command 全部留空，然后重新部署。

---

## 6. 部署后验证

按顺序点一遍，全过就是成功：

1. `https://你的域名.vercel.app/` → 「讲稿工坊」首页
2. `https://你的域名.vercel.app/api/health` → `{"status":"ok","db":"sqlite","llm":false}`
3. 点右上角「体验一下」→ 自动登录 demo
4. 「最近打开」里点示例文稿 → 选风格 → 生成讲稿
5. 「演讲模式」→ 能翻页、计时
6. 「Word」→ 能下载

---

## 7. 三条硬限制（提前知道，避免踩坑）

### ① 上传文件 ≤ 4MB

Vercel 函数请求体上限 4.5MB。含大图的 PPT 会失败。

**解决**：PowerPoint → 图片格式 → 压缩图片 → 选「电子邮件 96ppi」，通常能压到 2MB 内。

### ② 数据存在 `/tmp`，冷启动即清空

- 约 15 分钟没人访问 → 实例回收，数据重建（只剩 demo 账号和示例 PPT）
- 你上传的 PPT、讲稿历史会消失；多实例之间也不共享

演示过程中实例是热的，够用。要长期保存需接外部数据库（Neon Postgres 免费额度即可），改动点：`api/app/database.py` 的 `DATABASE_URL` + `requirements.txt` 加 `psycopg[binary]`。

### ③ 函数最长 60 秒

用大模型且页数很多时可能超时。**解决**：时长控制在 10 分钟内，或换更快模型。

---

## 8. 常见报错

| 报错 | 原因 | 处理 |
| --- | --- | --- |
| `[unused_function] The pattern "api/index.py" ...` | 旧版配置里声明了 `functions`，但函数没被识别 | **已修复**：新版 `vercel.json` 去掉了 `functions`，并把代码放进 `api/app/` |
| 构建 1 秒退出 | 配置校验失败，根本没开始构建 | 看 Build Logs 第二行起的具体报错 |
| `Cannot find module 'vite'` | 前端依赖没装 | 确认 `buildCommand` 是 `npm --prefix frontend install && npm --prefix frontend run build` |
| 首页 404 | `outputDirectory` 不生效 | 确认 `vercel.json` 里是 `"outputDirectory": "frontend/dist"` |
| `/api/health` 404 | Function 没匹配上 | 确认 `api/index.py` 在部署文件列表里；`rewrites` 第一条是 `/api/:path* → /api/index` |
| `/api/health` 500，日志 `ModuleNotFoundError` | 函数包里缺 `api/app/` | 确认打包时同步过：`python scripts/sync_api_backend.py` |
| 上传报「超过 4MB」 | 见第 7 节 ① | 压缩 PPT |
| 登录后刷新掉登录 | `SECRET_KEY` 每次变 | 在环境变量里固定 |

---

## 9. 如果 Vercel 的限制不能接受

这份作品是 31 页、近 5MB 的 PPT，Vercel 的 4MB 限制会卡住。项目自带 Docker 部署，任何云服务器（阿里云/腾讯云学生机都行）一条命令搞定：

```bash
docker compose up -d --build
# 打开 http://服务器公网IP:8080
```

有真正的磁盘、真正的 MySQL、没有 4MB 限制、没有 60 秒超时——更适合交作业的正式版本。
