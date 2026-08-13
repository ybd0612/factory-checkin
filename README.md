# New API 每日自动签到

适用于所有基于 [New API](https://github.com/QuantumNous/new-api) 搭建、且开启了「签到奖励」功能的站点的**每日自动签到工具**。

- ✅ 零依赖：仅使用 Python 标准库，Python 3.8+ 即可运行
- ✅ 智能跳过：先查询签到状态，当天已签到自动跳过，不会重复签到
- ✅ 自动重试：网络失败自动重试 3 次
- ✅ 两种运行方式：GitHub Actions 云端定时 / 本地手动或定时
- ✅ 通用化：通过环境变量配置站点地址，可用于任意 New API 站点

> 本项目默认站点为 `https://factory.pub`，其他站点只需修改站点地址配置。

## 前置准备：获取凭证

你需要两样东西：**访问令牌**和**用户 ID**。

### 1. 获取访问令牌（NEWAPI_TOKEN）

1. 登录站点
2. 进入「个人设置 → 安全设置（或账户管理）」
3. 找到「系统访问令牌」，点击**生成令牌**，复制生成的值

### 2. 获取用户 ID（NEWAPI_USER_ID）

1. 登录站点后按 `F12` 打开浏览器开发者工具
2. 切到 **Application（应用）** 面板
3. 左侧找到 **Local Storage → 站点域名 → `user`**
4. 其中 JSON 的 `id` 字段（一个数字）即为用户 ID

### 3.（可选）确认站点已开启签到

在浏览器中直接访问 `https://站点地址/api/user/checkin?month=YYYY-MM`（把 YYYY-MM 换成当前年月），若返回的 JSON 中 `enabled` 为 `true`，说明签到功能已开启。

## 方式一：GitHub Actions 云端定时运行（推荐）

无需服务器、无需开电脑，每天自动签到。获取代码有两种方式，任选其一：

- **方式 A：直接 Fork 本仓库**（最简单，推荐）：后续上游更新可一键同步；注意 fork 出的仓库是公开的，但安全性不受影响（见下方说明）
- **方式 B：新建私有仓库推送**：隐私性更强，但与上游脱钩，后续更新需手动同步

### 方式 A：Fork 后使用（推荐）

1. **Fork**：在本仓库页面右上角点击 **Fork**，创建属于你自己的副本
2. **配置 Secrets**：在你 fork 的仓库中，进入 **Settings → Secrets and variables → Actions → Secrets**，点击 **New repository secret**，分别创建：

   | Name | Value |
   |---|---|
   | `NEWAPI_TOKEN` | 你的访问令牌 |
   | `NEWAPI_USER_ID` | 你的数字用户 ID |

3. **（可选）配置站点地址**：如果你的站点不是默认的 `https://factory.pub`，切到 **Variables** 标签页，创建变量：

   | Name | Value |
   |---|---|
   | `NEWAPI_BASE_URL` | 你的站点地址，如 `https://your-site.com` |

4. **启用 Actions**：fork 出的仓库默认禁用 Actions。进入你 fork 仓库的 **Actions** 标签页，点击 **I understand my workflows, go ahead and enable them**
5. **手动测试一次**：Actions → 「每日签到」→ **Run workflow**，查看运行日志，应输出签到结果。

> 💡 后续上游代码更新时，在你 fork 的仓库页面点击 **Sync fork → Update branch** 即可同步。

#### 公开 fork 存放令牌安全吗？

安全。原因：

- Secrets 在 GitHub 上加密存储，不会出现在仓库代码或运行日志中，任何访客都看不到
- 他人向你的 fork 提交的 PR 无法获取你的 Secrets（GitHub 不会向外部 PR 触发的工作流传入 Secrets）
- 唯一泄露途径是自行修改工作流主动打印 Secret，正常使用不会发生

如果你仍然介意仓库公开，请使用方式 B。

### 方式 B：新建私有仓库

在 GitHub 上新建一个**私有仓库**（Private），将本项目代码推送上去：

```bash
git init
git add .
git commit -m "feat: newapi daily checkin"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

之后同样完成上面的第 2~5 步（配置 Secrets → 可选站点地址 → 启用 Actions → 手动测试）。

### 运行时间

工作流每天自动运行 3 次（北京时间 08:00 / 16:00 / 24:00）。GitHub Actions 定时触发可能有 1~2 小时延迟且偶尔漏触发，多次运行可确保不漏签；已签到的运行会自动跳过。

## 方式二：本地运行

适合想在自有服务器 / NAS / 电脑上配合 cron、任务计划程序运行的场景。可参考仓库中的 `.env.example` 模板准备环境变量。

### 手动执行

```bash
# Linux / macOS
export NEWAPI_TOKEN="你的访问令牌"
export NEWAPI_USER_ID="你的用户ID"
export NEWAPI_BASE_URL="https://your-site.com"   # 可选，默认 https://factory.pub
python3 checkin.py
```

```powershell
# Windows PowerShell
$env:NEWAPI_TOKEN = "你的访问令牌"
$env:NEWAPI_USER_ID = "你的用户ID"
$env:NEWAPI_BASE_URL = "https://your-site.com"   # 可选
python checkin.py
```

输出示例：

```
站点: https://factory.pub
用户: 4724
时间: 2026-08-13 08:00:00
签到成功！日期: 2026-08-13，获得 $0.062 额度，当前连签 5 天
```

### 定时运行

**Linux cron**（每天北京时间 8 点）：

```bash
crontab -e
# 添加：
0 8 * * * NEWAPI_TOKEN="xxx" NEWAPI_USER_ID="4724" NEWAPI_BASE_URL="https://your-site.com" /usr/bin/python3 /path/to/checkin.py >> /path/to/checkin.log 2>&1
```

**Windows 任务计划程序**：创建基本任务，触发器设为每天，操作为运行 `python checkin.py`，并在「环境变量」或启动脚本中配置上述三个环境变量。

## 配置项一览

| 环境变量 | 必填 | 说明 |
|---|---|---|
| `NEWAPI_TOKEN` | ✅ | 站点后台生成的系统访问令牌 |
| `NEWAPI_USER_ID` | ✅ | 数字用户 ID |
| `NEWAPI_BASE_URL` | ❌ | 站点地址，默认 `https://factory.pub` |

## 工作原理

脚本调用 New API 内置的签到接口：

1. `GET /api/user/checkin?month=YYYY-MM` 查询当月签到状态（含今日是否已签、连签天数、累计额度）
2. 若今日未签到，`POST /api/user/checkin` 执行签到
3. 请求头需携带 `Authorization: Bearer <令牌>` 与 `New-Api-User: <用户ID>`

## 常见问题

- **401 / Unauthorized**：令牌失效或与用户 ID 不匹配。重新生成令牌，或核对用户 ID 是否正确。
- **提示「该站点未开启签到功能」**：站点管理员未开启签到奖励，无解，联系站长。
- **Actions 不触发**：新仓库需先手动 Run 一次 workflow；长期不活跃的仓库 Actions 会被禁用，需重新启用。
- **想换站点**：只需修改 `NEWAPI_BASE_URL`，凭证换成新站点的即可。

## 免责声明

本项目仅供个人学习与研究使用。请在使用前确认遵守目标站点的服务条款，因使用本项目产生的一切后果由使用者自行承担。

## License

[MIT](LICENSE)
