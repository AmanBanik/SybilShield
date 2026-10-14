import os
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    # Dual-mode FalkorDB connection settings
    falkordb_url: Optional[str] = os.getenv("FALKORDB_URL", None)
    falkordb_host: str = os.getenv("FALKORDB_HOST", "localhost")
    falkordb_port: int = int(os.getenv("FALKORDB_PORT", "6379"))
    falkordb_username: Optional[str] = os.getenv("FALKORDB_USERNAME", None)
    falkordb_password: Optional[str] = os.getenv("FALKORDB_PASSWORD", None)
    falkordb_ssl: bool = os.getenv("FALKORDB_SSL", "false").lower() == "true"
    falkordb_graph: str = os.getenv("FALKORDB_GRAPH", "sybil_shield_demo")

    # MCP server configuration (stdio for local, sse for cloud)
    mcp_transport: str = os.getenv("MCP_TRANSPORT", "stdio")
    mcp_host: str = os.getenv("MCP_HOST", "0.0.0.0")
    mcp_port: int = int(os.getenv("MCP_PORT", "8000"))
    mcp_server_name: str = "SybilShield-MCP"
    agent_id: str = "SybilShield-Agent-01"


settings = Settings()
