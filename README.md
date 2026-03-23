# BeBetter

> MCP server & Web UI for traditional Chinese metaphysics — Qi Men Dun Jia, Da Liu Ren, Tai Yi, Plum Blossom Numerology, and BaZi (Four Pillars of Destiny), with AI-powered cross-analysis.

A full-stack application that calculates traditional Chinese divination charts and uses LLM to provide unified interpretations. Available as a **Claude Code MCP server** or a standalone **Web UI**.

## Tech Stack

- **Core**: Python (chart calculation & AI interpretation)
- **MCP Server**: FastMCP (Model Context Protocol for Claude Code)
- **Backend**: FastAPI
- **Frontend**: Next.js + TypeScript + Tailwind CSS
- **Deployment**: Docker

---

## Features / 功能

- **Qi Men Dun Jia (奇門遁甲)** — Strategic action analysis
- **Da Liu Ren (大六壬)** — Event development prediction
- **Tai Yi Shen Shu (太乙神數)** — Force comparison
- **Plum Blossom Numerology (梅花易數)** — Quick divination (Ti-Yong analysis)
- **BaZi (八字)** — Four Pillars natal chart & compatibility analysis
- **Cross-Analysis (合參解讀)** — AI cross-references all charts for unified interpretation

## Architecture / 架構

```
bebetter/
├── core/       # Shared logic: chart calculation, AI interpretation
├── backend/    # FastAPI (Web UI backend)
├── frontend/   # Next.js + TypeScript (Web UI)
└── mcp/        # MCP Server (for Claude Code integration)
```

---

## MCP Server

讓 Claude Code 直接呼叫排盤工具。有兩種使用方式：

### 方式一：HTTP 模式（本地開發推薦）

MCP 本身不裝排盤依賴，輕量啟動，排盤請求轉發給 Backend API。

> 適合本地開發：`sxtwl` 等 C extension 在 macOS 上無法編譯，用 HTTP 繞過。

```bash
# 1. 先啟動 Backend（Docker）
make up-bebetter        # 或 docker compose up -d

# 2. 註冊 MCP（指向本機的 server.py）
claude mcp add -s user bebetter -- uv run --directory /path/to/bebetter/mcp python server.py
```

MCP 會自動偵測 `import core` 失敗 → fallback 到打 `BEBETTER_API_BASE`（預設 `https://bebetter.localtest.me/api`）。

### 方式二：Docker 模式（部署 / 分享推薦）

MCP 打包成 Docker image，core 和所有依賴都在容器裡，自給自足，不需要 Backend。

```bash
# Build
git clone https://github.com/teddy13643/bebetter.git
cd bebetter
docker build -t bebetter-mcp -f mcp/Dockerfile .
```

在 Claude Code 的 MCP 設定（`~/.claude.json`）加入：

```json
{
  "bebetter": {
    "command": "docker",
    "args": [
      "run",
      "-i",
      "--rm",
      "-e",
      "LLM_API_KEY=你的Groq_API_Key",
      "teddy13643/bebetter-mcp"
    ]
  }
}
```

也可以直接拉 image：

```bash
docker pull teddy13643/bebetter-mcp
```

### 兩種模式的差異

|          | HTTP 模式                    | Docker 模式      |
| -------- | ---------------------------- | ---------------- |
| **依賴** | 只需 `mcp` + `httpx`         | 全部打包在容器裡 |
| **前提** | Backend 要跑著               | 只需 Docker      |
| **適合** | 本地開發（Mac 裝不了 sxtwl） | 部署、分享給別人 |
| **速度** | 多一次 HTTP 來回             | 直接算，較快     |

### 可用 Tools

| Tool        | 說明               | 參數                                             |
| ----------- | ------------------ | ------------------------------------------------ |
| `interpret` | 四式合參 + AI 解讀 | `year`, `month`, `day`, `hour`, `minute`（西曆） |

一次排出奇門遁甲、大六壬、太乙神數、梅花易數四張盤，再用 AI 統整解讀。

### 環境變數

| 變數                | 必填 | 預設值                              | 說明                              |
| ------------------- | ---- | ----------------------------------- | --------------------------------- |
| `LLM_API_KEY`       | 是   | —                                   | LLM API Key（Groq / OpenAI 相容） |
| `LLM_BASE_URL`      | 否   | `https://api.groq.com/openai/v1`    | LLM API 端點                      |
| `LLM_MODEL`         | 否   | `llama-3.3-70b-versatile`           | 模型名稱                          |
| `BEBETTER_API_BASE` | 否   | `https://bebetter.localtest.me/api` | HTTP 模式的 Backend URL           |

---

## Web UI

### 啟動

```bash
docker compose up -d
```

- 前端：`http://localhost:3000`
- API：`http://localhost:8000/api`

### API Endpoints

| Method | Path             | 說明               |
| ------ | ---------------- | ------------------ |
| POST   | `/api/interpret` | 四式合參 + AI 解讀 |
| GET    | `/api/health`    | 健康檢查           |

Request body：

```json
{
  "year": 1991,
  "month": 1,
  "day": 13,
  "hour": 2,
  "minute": 40
}
```

---

## 排盤庫

- [kinqimen](https://github.com/kentang2017/kinqimen) — 奇門遁甲
- [kinliuren](https://github.com/kentang2017/kinliuren) — 大六壬
- [kintaiyi](https://github.com/kentang2017/kintaiyi) — 太乙神數
- [sxtwl](https://github.com/yuangu/sxtwl_cpp) — 萬年曆（干支轉換）

## License

MIT
