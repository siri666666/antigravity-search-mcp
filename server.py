#!/usr/bin/env python3
"""
antigravity-search-mcp

Extracts Google Antigravity's native search & web-reading toolchain
into a universal Model Context Protocol (MCP) server for any coding agent
(Codex, Claude Code, Cursor, Windsurf, Aider, etc.).

Tools exposed:
  1. `search_web`: Performs real-time Google Grounding search via Antigravity/Gemini.
  2. `read_url_content`: Fetches and extracts clean, readable Markdown from a web page.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

__version__ = "0.1.0"

# Upstream Antigravity Gateway URL (e.g. your sub2api or direct endpoint)
ANTIGRAVITY_BASE_URL = os.environ.get("ANTIGRAVITY_BASE_URL") or "https://sub2api.adq.ccwu.cc"
ANTIGRAVITY_API_KEY = os.environ.get("ANTIGRAVITY_API_KEY") or os.environ.get("SUB2API_API_KEY", "")

# Fallback token if not set in environment (check local codex config)
if not ANTIGRAVITY_API_KEY:
    config_path = os.path.expanduser("~/.codex/agy.config.toml")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "experimental_bearer_token" in line and "sk-" in line:
                        m = re.search(r'"(sk-[^"]+)"', line)
                        if m:
                            ANTIGRAVITY_API_KEY = m.group(1)
                            break
        except Exception:
            pass

TOOLS = [
    {
        "name": "search_web",
        "description": (
            "Performs a web search for a given query using Google Antigravity's native search engine. "
            "Returns a structured summary of relevant real-time information along with verified source citations."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query or keywords to look up on Google."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "read_url_content",
        "description": (
            "Fetches and extracts clean, readable text/Markdown from a specified web page URL. "
            "Useful for reading documentation, technical blogs, or news sources found from search_web."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The HTTP or HTTPS URL of the web page to read."
                },
                "max_chars": {
                    "type": "integer",
                    "default": 10000,
                    "description": "Maximum number of characters to extract (default 10000)."
                }
            },
            "required": ["url"]
        }
    }
]


def execute_google_search(query: str) -> str:
    """Calls Antigravity's native Google Grounding search."""
    endpoint = ANTIGRAVITY_BASE_URL.rstrip("/")
    if not endpoint.endswith("/v1/responses") and not endpoint.endswith("/responses"):
        endpoint += "/v1/responses"

    payload = {
        "model": "gemini-3.8-flash",
        "input": [
            {
                "role": "user",
                "content": f"请针对以下检索主题搜索网络并提取核心事实摘要与相关来源链接：\n{query}"
            }
        ],
        "tools": [
            {"type": "web_search_20250305"}
        ]
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "antigravity-search-mcp/0.1.0",
            "Authorization": f"Bearer {ANTIGRAVITY_API_KEY}"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            res_data = json.loads(resp.read().decode("utf-8", errors="replace"))
            text_blocks = []
            for item in res_data.get("output", []):
                if item.get("type") == "message":
                    for c in item.get("content", []):
                        if c.get("type") == "output_text":
                            text_blocks.append(c.get("text", ""))
            if text_blocks:
                return "\n\n".join(text_blocks).strip()
            return "No search results returned."
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return f"Google Search Error (HTTP {e.code}): {err_body}"
    except Exception as e:
        return f"Google Search Connection Error: {str(e)}"


def execute_read_url(url: str, max_chars: int = 10000) -> str:
    """Fetches and cleans page text into Markdown-like summary."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "").lower()
            raw_bytes = resp.read()
            
            # Encoding detection
            encoding = "utf-8"
            if "charset=" in content_type:
                encoding = content_type.split("charset=")[-1].split(";")[0].strip()
            
            try:
                html = raw_bytes.decode(encoding, errors="replace")
            except Exception:
                html = raw_bytes.decode("utf-8", errors="replace")

            # Basic HTML to clean text extraction (stdlib only)
            # Remove script, style, comments
            html = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
            
            # Format headers and links
            html = re.sub(r"<h[1-6][^>]*>(.*?)</h[1-6]>", r"\n\n### \1\n", html, flags=re.IGNORECASE)
            html = re.sub(r"<p[^>]*>", "\n\n", html, flags=re.IGNORECASE)
            html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
            html = re.sub(r"<li[^>]*>", "\n- ", html, flags=re.IGNORECASE)
            
            # Strip remaining tags
            text = re.sub(r"<[^>]+>", "", html)
            
            # Clean excess whitespace
            text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
            
            if len(text) > max_chars:
                text = text[:max_chars] + f"\n\n...[Truncated: content exceeded {max_chars} characters]"
            return text if text else "Page loaded but no readable text found."
    except Exception as e:
        return f"Failed to read URL '{url}': {str(e)}"


HANDLERS = {
    "search_web": lambda args: execute_google_search(args.get("query", "")),
    "read_url_content": lambda args: execute_read_url(args.get("url", ""), args.get("max_chars", 10000))
}


def handle_rpc(msg: dict) -> dict:
    method = msg.get("method")
    if method == "initialize":
        return {
            "protocolVersion": msg.get("params", {}).get("protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "antigravity-search-mcp",
                "version": __version__
            }
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        params = msg.get("params", {})
        name = params.get("name")
        handler = HANDLERS.get(name)
        if not handler:
            raise LookupError(f"Unknown tool: {name}")
        try:
            res_text = handler(params.get("arguments") or {})
            return {"content": [{"type": "text", "text": str(res_text)}], "isError": False}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}
    raise LookupError(f"Method not found: {method}")


def main():
    out = sys.stdout.buffer
    for line in sys.stdin.buffer:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if "id" not in msg:
            continue
        try:
            reply = {"jsonrpc": "2.0", "id": msg["id"], "result": handle_rpc(msg)}
        except LookupError as e:
            reply = {"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32601, "message": str(e)}}
        out.write(json.dumps(reply, ensure_ascii=False).encode("utf-8") + b"\n")
        out.flush()


if __name__ == "__main__":
    main()
