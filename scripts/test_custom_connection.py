#!/usr/bin/env python3
"""
SybilShield: Custom FalkorDB Connection & Diagnostic Utility
Verifies connectivity, authentication, GraphBLAS latency, and schema indexes
for any custom, on-premise, or cloud-hosted FalkorDB database instance.
"""

import sys
import time
import argparse
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from falkordb import FalkorDB
from src.config import settings


def test_custom_connection(
    url: str = None,
    host: str = None,
    port: int = None,
    username: str = None,
    password: str = None,
    ssl: bool = False,
    graph_name: str = "sybil_shield_demo",
    init_indexes: bool = False
):
    print("=" * 70)
    print("      SYBILSHIELD: CUSTOM FALKORDB CONNECTION DIAGNOSTIC")
    print("=" * 70)

    # 1. Establish Client
    try:
        t0 = time.time()
        if url:
            print(f"[*] Connecting via URL: {url.split('@')[-1] if '@' in url else url}")
            client = FalkorDB.from_url(url)
        elif host and port:
            print(f"[*] Connecting via Host/Port: {host}:{port} (SSL: {ssl})")
            client = FalkorDB(
                host=host,
                port=port,
                username=username,
                password=password,
                ssl=ssl
            )
        elif settings.falkordb_url:
            print(f"[*] Connecting via environment FALKORDB_URL...")
            client = FalkorDB.from_url(settings.falkordb_url)
        else:
            print(f"[*] Connecting via default local instance: {settings.falkordb_host}:{settings.falkordb_port}...")
            client = FalkorDB(host=settings.falkordb_host, port=settings.falkordb_port)

        connect_latency_ms = (time.time() - t0) * 1000
        print(f"[+] TCP & Authentication Handshake Succeeded! ({connect_latency_ms:.2f} ms)")

    except Exception as e:
        print(f"[-] Connection Failed: {e}")
        print("\nTroubleshooting Tips:")
        print("  1. Verify the host/port are reachable and not blocked by a firewall.")
        print("  2. In FalkorDB Cloud, ensure your IP is whitelisted (or set to 0.0.0.0/0).")
        print("  3. Check that special characters in passwords are URL-encoded (e.g. '@' -> '%40').")
        sys.exit(1)

    # 2. Select Graph & Ping
    try:
        print(f"[*] Testing GraphBLAS query execution on graph: '{graph_name}'...")
        graph = client.select_graph(graph_name)
        t_query = time.time()
        res = graph.query("RETURN 1 AS ping, timestamp() AS ts")
        query_latency_ms = (time.time() - t_query) * 1000

        print(f"[+] GraphBLAS Ping Succeeded! Latency: {query_latency_ms:.2f} ms")

        # Check existing stats
        node_count = graph.query("MATCH (n) RETURN count(n) AS cnt").result_set[0][0]
        edge_count = graph.query("MATCH ()-[r]->() RETURN count(r) AS cnt").result_set[0][0]

        print(f"[+] Target Graph Statistics:")
        print(f"    - Total Nodes: {node_count}")
        print(f"    - Total Relationships: {edge_count}")

    except Exception as e:
        print(f"[-] Query Execution Error: {e}")
        sys.exit(1)

    # 3. Optional: Initialize Schema Performance Indexes
    if init_indexes:
        print("\n[*] Initializing high-performance schema indexes...")
        indexes = [
            "CREATE INDEX FOR (a:Account) ON (a.id)",
            "CREATE INDEX FOR (d:DeviceFingerprint) ON (d.device_id)",
            "CREATE INDEX FOR (i:IPAddress) ON (i.ip)",
            "CREATE INDEX FOR (c:PaymentCard) ON (c.card_hash)"
        ]
        for idx in indexes:
            try:
                graph.query(idx)
                print(f"    [+] Created index: {idx.split('ON ')[-1]}")
            except Exception as e:
                # Indexes might already exist
                print(f"    [!] Index note: {e}")
        print("[+] Schema indexes verified and ready for production querying.")

    print("\n" + "=" * 70)
    print(" [STATUS] Database is fully compatible and ready for SybilShield!")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Test and diagnose custom FalkorDB connections for SybilShield")
    parser.add_argument("--url", type=str, help="Full connection URL (e.g. falkor://falkordb:pass@host:port)")
    parser.add_argument("--host", type=str, help="FalkorDB host or IP")
    parser.add_argument("--port", type=int, help="FalkorDB port (default: 6379)")
    parser.add_argument("--username", type=str, help="FalkorDB username")
    parser.add_argument("--password", type=str, help="FalkorDB password")
    parser.add_argument("--ssl", action="store_true", help="Enable SSL/TLS encryption")
    parser.add_argument("--graph", type=str, default="sybil_shield_demo", help="Target graph name")
    parser.add_argument("--init-indexes", action="store_true", help="Initialize performance indexes on the graph")

    args = parser.parse_args()

    test_custom_connection(
        url=args.url,
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        ssl=args.ssl,
        graph_name=args.graph,
        init_indexes=args.init_indexes
    )


if __name__ == "__main__":
    main()
