# Reusable Skills

可复用的 Codex / OpenCode 风格 Agent Skills 集合。

本仓库把个人项目中的通用能力拆成可以独立安装的 Skill：

- 游戏开发方法型 Skills：直接可复用；
- 招聘自动化项目中的通用逻辑：去掉 BOSS、SQLite、飞书和固定路径后重构；
- 每个 Skill 都保持独立目录，以便被其他项目或用户单独安装。

## 当前包含

| Skill | 类型 | 说明 |
|---|---|---|
| `dialogue-systems` | portable | 分支对话、Ink、Yarn Spinner、数据驱动对话图 |
| `game-feel` | portable | Screen shake、hit-stop、easing、受击反馈和游戏打击感 |
| `game-ui-design` | portable | HUD、菜单、库存、游戏界面设计 |
| `game-ui-ux` | portable | 响应式布局、安全区、焦点导航、事件驱动 HUD |
| `visual-novel` | portable | 视觉小说、互动叙事、存档、回看和自动播放 |
| `jd-hard-requirement-matcher` | refactored | 通用硬性要求匹配和证据化判断 |
| `daily-automation-report` | refactored | 自动化日报生成和数据一致性校验 |
| `weekly-automation-report` | refactored | 自动化周报、趋势和风险汇总 |
| `record-exporter` | refactored | 结构化记录的分组导出和只读归档 |
| `github-project-memory` | portable | 扫描 GitHub 项目与 SKILL.md，并保存可查询的本地记忆 |
| `finance-quant-backtesting` | personal | 个人量化数据、策略回测、因子分析和风险评估 |

完整清单见 [`manifest.json`](manifest.json)。

## GitHub 项目记忆

`github-project-memory` 用于把指定 GitHub 账号的仓库和 `SKILL.md` 清单保存为本地索引，后续查询优先读取索引，不必每次重新扫描。它只保存仓库/Skill 元数据，不保存 Token、Cookie、私有源码或仓库完整内容。

首次使用时，建议先在本机完成登录：

```powershell
gh auth login
python .\skills\github-project-memory\scripts\github_project_memory.py auth
```

也可以使用环境变量 `GITHUB_TOKEN` 或 `GH_TOKEN`；不要把 Token 粘贴到聊天中。扫描公开仓库不强制登录，扫描 private 或全部仓库需要已认证账号。

```powershell
# 扫描公开仓库
python .\skills\github-project-memory\scripts\github_project_memory.py scan --owner lbql-yhl --scope public

# 扫描当前已登录账号的公开和私有仓库
python .\skills\github-project-memory\scripts\github_project_memory.py scan --owner https://github.com/lbql-yhl --scope all

# 从本地记忆快速列出或查询
python .\skills\github-project-memory\scripts\github_project_memory.py list
python .\skills\github-project-memory\scripts\github_project_memory.py find game-ui
```

默认记忆文件是 `~/.codex/memory/github-projects.json`，可通过 `GITHUB_PROJECT_MEMORY_PATH` 或 `--memory-path` 修改。

## 一键安装

### macOS / Linux

安装全部 Skills：

```bash
curl -fsSL https://raw.githubusercontent.com/lbql-yhl/codex-skills/main/install.sh | bash
```

只安装指定 Skill：

```bash
curl -fsSL https://raw.githubusercontent.com/lbql-yhl/codex-skills/main/install.sh | bash -s -- game-feel dialogue-systems
```

### Windows PowerShell

安装全部 Skills：

```powershell
irm https://raw.githubusercontent.com/lbql-yhl/codex-skills/main/install.ps1 | iex
```

只安装指定 Skill：

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/lbql-yhl/codex-skills/main/install.ps1))) -Skill game-feel,dialogue-systems
```

如果希望安装到指定目录：

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/lbql-yhl/codex-skills/main/install.ps1))) -Skill game-feel -Target C:\Users\you\.codex\skills
```

> 上面的 GitHub 地址假定仓库最终命名为 `lbql-yhl/codex-skills`。如果仓库名称不同，可设置 `SKILLS_REPO_URL` 环境变量，或修改两个安装脚本中的默认地址。

## 本地安装

克隆仓库后运行：

```bash
python3 bin/install.py --list
python3 bin/install.py --all
python3 bin/install.py game-feel dialogue-systems
python3 bin/install.py --target ./test-skills game-feel
```

Windows：

```powershell
python .\bin\install.py --list
python .\bin\install.py game-feel dialogue-systems
```

默认安装目标：

1. `CODEX_SKILLS_DIR` 环境变量；
2. `$CODEX_HOME/skills`；
3. `~/.codex/skills`。

安装器只会复制指定 Skill 目录，不会删除目标目录中的其他 Skill。每个已安装 Skill 会写入 `.reusable-skill.json` 记录来源和版本状态。

## 在其他项目中使用

安装后，Agent 会从目标 Skills 目录发现这些 Skill。也可以直接把某个目录复制到项目自己的 Skill 目录：

```text
your-project/
└── .codex/
    └── skills/
        └── game-feel/
            ├── SKILL.md
            └── references/
```

不要只复制 `SKILL.md`；带有 `references/` 的 Skill 必须保留整个目录。

## 复用等级

### `portable`

可以直接放到其他项目使用，通常不依赖脚本、数据库、账号、浏览器会话或外部服务。

### `refactored`

从具体业务项目中提炼出的通用版本。它保留原项目中有价值的判断逻辑，但已经移除：

- BOSS / Zhipin 专用流程；
- 固定 SQLite 路径和数据库表；
- 固定飞书群和联系人；
- 机器相关绝对路径；
- 账号、浏览器和运行时状态。

这些 Skill 需要调用方提供结构化输入和输出目标。

## 设计原则

- 每个 Skill 都有独立的 `SKILL.md`；
- 可选的长文档放在 `references/`；
- 安装器支持按名称安装，不强制安装全部内容；
- 不把凭据、浏览器会话、真实数据库和运行时目录打包进仓库；
- 只读和报告型 Skill 默认不修改源数据；
- `manifest.json` 是安装器的唯一索引来源。

## 来源说明

- `dialogue-systems`、`game-feel`、`game-ui-design`、`game-ui-ux`、`visual-novel`：整理自 `open-world-game-1.0` 项目的 `.opencode/skills/`。
- `jd-hard-requirement-matcher`：由 `zhineng-zhaopin-jiqiren` 的 JD 匹配逻辑重构。
- `daily-automation-report`：由招聘机器人日报逻辑重构。
- `weekly-automation-report`：由招聘机器人周报逻辑重构。
- `record-exporter`：由招聘机器人桌面归档逻辑重构。

## 发布前检查

```bash
python -m unittest discover -s tests -v
python bin/install.py --dry-run --all
```

如果本机安装了 Codex Skill Creator 校验器，还可以对每个 Skill 运行 `quick_validate.py`。
