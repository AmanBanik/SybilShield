import sys
from pathlib import Path

# Ensure project root is in sys.path regardless of working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Any, Dict, List
from fastmcp import FastMCP
from src.config import settings
from src.db.queries import FraudGraphQueries

mcp = FastMCP(settings.mcp_server_name)


@mcp.tool()
def investigate_account(account_id: str) -> Dict[str, Any]:
    """Inspects an account's 1-hop profile, including attached devices, IPs, cards, and direct transfer activity.
    
    Args:
        account_id: Unique account identifier (e.g. 'MULE_A' or 'ACC_ALICE').
    """
    profile = FraudGraphQueries.get_account_neighborhood(account_id)
    if not profile:
        return {"error": f"Account '{account_id}' was not found in the graph."}
    return profile


@mcp.tool()
def detect_sybil_ring(account_id: str, max_hops: int = 2) -> List[Dict[str, Any]]:
    """Performs multi-hop graph expansion to find accomplice accounts sharing hardware fingerprints, VPN IPs, or payment cards.
    
    Args:
        account_id: Seed account identifier to expand the cluster from.
        max_hops: Hop depth for vector expansion (default: 2).
    """
    return FraudGraphQueries.detect_sybil_ring(account_id, max_hops=max_hops)


@mcp.tool()
def trace_fund_cycles(account_id: str, max_hops: int = 5) -> List[Dict[str, Any]]:
    """Detects circular money laundering cycles (e.g., A -> B -> C -> D -> A) routing funds back to the origin.
    
    Args:
        account_id: Account identifier to inspect for cyclic paths.
        max_hops: Maximum path length to evaluate for cycles (default: 5).
    """
    return FraudGraphQueries.trace_fund_cycles(account_id, max_hops=max_hops)


@mcp.tool()
def calculate_ring_centrality(top_k: int = 10) -> List[Dict[str, Any]]:
    """Runs FalkorDB native PageRank across the transfer network to pinpoint key cash-out mules and coordinator nodes.
    
    Args:
        top_k: Number of highest-ranked accounts to return (default: 10).
    """
    return FraudGraphQueries.calculate_centrality(algorithm="pagerank", top_k=top_k)


@mcp.tool()
def execute_mitigation(action: str, account_ids: List[str], reason: str) -> Dict[str, Any]:
    """Executes defensive actions on identified fraud networks by freezing accounts, blacklisting shared vectors, and logging an immutable audit record in FalkorDB.
    
    Args:
        action: Defensive action to perform ('FREEZE', 'THROTTLE_VELOCITY', or 'FLAG_HIGH_RISK').
        account_ids: List of account IDs to apply the mitigation to.
        reason: Forensic justification explaining the graph topology and evidence.
    """
    return FraudGraphQueries.execute_mitigation(
        action=action,
        account_ids=account_ids,
        reason=reason,
        agent_id=settings.agent_id
    )


@mcp.tool()
def blacklist_compromised_instrument(instrument_type: str, instrument_id: str, reason: str) -> Dict[str, Any]:
    """Blacklists a compromised hardware device or stolen payment card directly in FalkorDB to block network-wide reuse.
    
    Args:
        instrument_type: Type of instrument ('DEVICE' or 'CARD').
        instrument_id: Device ID (e.g., 'DEV_GHOST_EMULATOR_88') or Card Hash (e.g., 'CARD_VISA_STOLEN_9901').
        reason: Forensic justification for the block.
    """
    from src.mitigation.engine import MitigationEngine
    if instrument_type.upper() == "DEVICE":
        return MitigationEngine.execute(action="BLACKLIST_DEVICE", device_ids=[instrument_id], reason=reason)
    else:
        return MitigationEngine.execute(action="BLACKLIST_CARD", card_hashes=[instrument_id], reason=reason)


@mcp.tool()
def investigate_natural_language_prompt(prompt: str) -> Dict[str, Any]:
    """Autonomous end-to-end investigation tool that parses any freeform incident alert or natural language query,
    resolves mentioned entities (accounts, stolen cards, rogue devices) in FalkorDB, traverses the multi-hop topology,
    and returns the forensic verdict and SAR report.
    
    Args:
        prompt: Any freeform incident report or query (e.g., 'Card CARD_VISA_STOLEN_9901 stolen, check MULE_E and freeze accomplices').
    """
    from src.agent.core import SybilShieldAgent
    agent = SybilShieldAgent()
    return agent.investigate_prompt(prompt)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SybilShield FastMCP Server")
    parser.add_argument(
        "--transport", "-t",
        default=settings.mcp_transport,
        choices=["stdio", "sse"],
        help="MCP transport protocol ('stdio' for local Claude Desktop, 'sse' for cloud HTTP stream)"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=settings.mcp_port,
        help="Port for SSE transport (default: 8000)"
    )
    parser.add_argument(
        "--host",
        default=settings.mcp_host,
        help="Host interface for SSE transport (default: 0.0.0.0)"
    )
    args = parser.parse_args()

    if args.transport == "sse":
        print(f"[*] Starting SybilShield FastMCP Server with SSE on http://{args.host}:{args.port}/sse ...")
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")
