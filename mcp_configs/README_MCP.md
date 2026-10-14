# SybilShield MCP Client Integration Manual

This directory contains configuration files and client harnesses for connecting SybilShield FastMCP to various AI environments.

---

## 1. Claude Desktop (Windows)

1. Open (or create) your Claude Desktop configuration file:
   `%APPDATA%\Claude\claude_desktop_config.json`
2. Copy the contents of [`claude_desktop_config.json`](./claude_desktop_config.json):
   ```json
   {
     "mcpServers": {
       "sybilshield": {
         "command": "C:\\Devfield\\devhack\\SybilShield\\.venv\\Scripts\\python.exe",
         "args": ["-m", "src.mcp.server"],
         "cwd": "C:\\Devfield\\devhack\\SybilShield",
         "env": {
           "FALKORDB_HOST": "localhost",
           "FALKORDB_PORT": "6379",
           "FALKORDB_GRAPH": "sybil_shield_demo"
         }
       }
     }
   }
   ```
3. Restart Claude Desktop.
4. Verify the hammer icon appears in the chat box with the 6 tools registered.

---

## 2. Cursor IDE

1. Open your workspace settings or create `.cursor/mcp.json` in your repository root.
2. Paste the configuration from [`cursor_mcp.json`](./cursor_mcp.json).
3. Cursor AI Chat will now automatically call `investigate_account()`, `detect_sybil_ring()`, and `execute_mitigation()` when prompted about fraud investigations.

---

## 3. Python AI Agent Harness (`gemini_agent_harness.py`)

You can run automated multi-turn tool-calling loops directly from the terminal without external desktop apps:

```bash
# Run on any of the 10 scenarios (1 through 10)
python -m mcp_configs.gemini_agent_harness --scenario 1
python -m mcp_configs.gemini_agent_harness --scenario 2
python -m mcp_configs.gemini_agent_harness --scenario 4
python -m mcp_configs.gemini_agent_harness --scenario 9
```

---

## 4. HTTP / SSE Transport for Web Clients

To expose SybilShield over HTTP/SSE (for web assistants, LibreChat, or remote agents):
```bash
# Start FastMCP with SSE transport on port 8000
python -c "from src.mcp.server import mcp; mcp.run(transport='sse', port=8000)"
```
Endpoint: `http://localhost:8000/sse`
