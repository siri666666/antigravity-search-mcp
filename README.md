# antigravity-search-mcp 🔍

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-success.svg)](https://modelcontextprotocol.io)

**将 Google Antigravity (`agy`) 官方强大的实时搜索与网页阅读工具链，解耦并移植为通用的 Model Context Protocol (MCP) 服务器。**

赋能所有 AI 编程 Agent（如 **Codex**、**Claude Code**、**Cursor**、**Windsurf**、**Aider** 等），让它们在拥有本地文件修改与命令行执行能力的同时，也能零冲突、无损享有 Google 原生实时接地（Grounding）搜索体验。

---

## 💡 为什么需要它？

在传统方案中，当 AI 客户端（如 Codex）挂载了本地终端或改代码工具（Function Declarations）时，Google 的底模接口严格禁止混用官方的云端插件（会直接报错 `400 Bad Request`）。这导致大量 Agent 在查阅最新资料时，只能笨拙地在用户电脑中通过命令行手写 Python/curl 爬虫。

**`antigravity-search-mcp` 的解决方案：**
- 逆向并提取了 Google 官方 CLI（`agy`）的内部多轮闭环调度机制；
- 暴露标准的 `search_web` 与 `read_url_content` 客户端工具；
- **0 额外费用**：直接复用你现有的 Antigravity / Gemini 渠道，无需单独花钱购买任何第三方收费搜索 API（如 Tavily / Serper）。

---

## 🛠️ 包含工具 (Exposed Tools)

| 工具名称 | 功能描述 |
| :--- | :--- |
| **`search_web`** | 调用 Antigravity 原生 Google Grounding 进行实时网络检索，返回权威摘要与来源引用。 |
| **`read_url_content`** | 针对搜索出的技术文档、博客或 GitHub 页面进行降噪阅读与 Markdown 提取。 |

---

## 🚀 接入配置

本服务使用标准 Python 3 标准库编写，**无需安装任何额外 pip 依赖**，极简部署。

### 1. 配置到 Codex (`config.toml`)

在你的 `~/.codex/config.toml` 或对应 profile 的配置中添加：

```toml
[mcp_servers.antigravity_search]
command = "python"
args = ["C:/path/to/antigravity-search-mcp/server.py"]
startup_timeout_sec = 30
tool_timeout_sec = 60
default_tools_approval_mode = "approve"

[mcp_servers.antigravity_search.env]
ANTIGRAVITY_BASE_URL = "https://your-sub2api-domain.com"
ANTIGRAVITY_API_KEY = "sk-xxxxxxxx"
```

### 2. 配置到 Claude Code (`claude.json`)

```json
{
  "mcpServers": {
    "antigravity_search": {
      "command": "python",
      "args": ["/path/to/antigravity-search-mcp/server.py"],
      "env": {
        "ANTIGRAVITY_BASE_URL": "https://your-sub2api-domain.com",
        "ANTIGRAVITY_API_KEY": "sk-xxxxxxxx"
      }
    }
  }
}
```

### 3. 配置到 Cursor / Windsurf

在 MCP 配置文件中添加 stdio 命令：
- **Command**: `python`
- **Args**: `["/path/to/antigravity-search-mcp/server.py"]`

---

## 📄 环境变量说明

- `ANTIGRAVITY_BASE_URL`：sub2api 网关或 Antigravity 端点地址（默认支持 `/v1/responses`）。
- `ANTIGRAVITY_API_KEY`：用于鉴权的 API 密钥或 Bearer Token。

---

## 📜 开源协议

本项目采用 [MIT License](LICENSE) 授权。
