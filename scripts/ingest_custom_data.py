#!/usr/bin/env python3
"""
SybilShield: Custom Banking Data Ingestion Utility
Imports external banking ledger CSVs/JSONs into FalkorDB, constructing
the interconnected graph topology of accounts, devices, cards, and fund transfers.
"""

import csv
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


def ingest_banking_csv(
    csv_path: str,
    url: str = None,
    host: str = None,
    port: int = None,
    graph_name: str = "sybil_shield_demo",
    clear_existing: bool = False
):
    print("=" * 70)
    print("        SYBILSHIELD: CUSTOM BANKING DATA INGESTION PIPELINE")
    print("=" * 70)

    # 1. Connect to Target FalkorDB
    if url:
        print(f"[*] Target Engine: FalkorDB via URL ({url.split('@')[-1] if '@' in url else url})")
        db = FalkorDB.from_url(url)
    elif host and port:
        print(f"[*] Target Engine: FalkorDB at {host}:{port}")
        db = FalkorDB(host=host, port=port)
    elif settings.falkordb_url:
        print(f"[*] Target Engine: FalkorDB Cloud ({settings.falkordb_url.split('@')[-1]})")
        db = FalkorDB.from_url(settings.falkordb_url)
    else:
        print(f"[*] Target Engine: Local FalkorDB ({settings.falkordb_host}:{settings.falkordb_port})")
        db = FalkorDB(host=settings.falkordb_host, port=settings.falkordb_port)

    # 2. Select / Clear Graph
    if clear_existing:
        try:
            db.select_graph(graph_name).delete()
            print(f"[*] Cleared existing graph '{graph_name}'.")
        except Exception:
            pass

    graph = db.select_graph(graph_name)

    # 3. Create Performance Indexes
    indexes = [
        "CREATE INDEX FOR (a:Account) ON (a.id)",
        "CREATE INDEX FOR (d:DeviceFingerprint) ON (d.device_id)",
        "CREATE INDEX FOR (i:IPAddress) ON (i.ip)",
        "CREATE INDEX FOR (c:PaymentCard) ON (c.card_hash)"
    ]
    for idx in indexes:
        try:
            graph.query(idx)
        except Exception:
            pass

    # 4. Ingest CSV Rows
    print(f"[*] Reading banking ledger from: {csv_path}...")
    t0 = time.time()
    row_count = 0

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sender = row["sender_id"].strip()
            receiver = row["receiver_id"].strip()
            amount = float(row.get("amount", 0.0))
            device = row.get("sender_device", "").strip()
            ip = row.get("sender_ip", "").strip()
            card = row.get("sender_card", "").strip()
            is_emulator = row.get("is_emulator", "false").lower() == "true"
            is_vpn = row.get("is_vpn", "false").lower() == "true"

            # Cypher parameterized transaction insertion
            cypher = """
            MERGE (s:Account {id: $sender})
            ON CREATE SET s.status = 'ACTIVE', s.risk_score = 10, s.created_at = timestamp()

            MERGE (r:Account {id: $receiver})
            ON CREATE SET r.status = 'ACTIVE', r.risk_score = 10, r.created_at = timestamp()

            CREATE (s)-[:TRANSFERRED {amount: $amount, timestamp: timestamp()}]->(r)
            """
            params = {"sender": sender, "receiver": receiver, "amount": amount}

            # Link Device if present
            if device:
                cypher += """
                MERGE (d:DeviceFingerprint {device_id: $device})
                ON CREATE SET d.is_emulator = $is_emulator, d.status = 'ACTIVE'
                MERGE (s)-[:USED_DEVICE]->(d)
                """
                params["device"] = device
                params["is_emulator"] = is_emulator

            # Link IP if present
            if ip:
                cypher += """
                MERGE (i:IPAddress {ip: $ip})
                ON CREATE SET i.is_vpn = $is_vpn
                MERGE (s)-[:USED_IP]->(i)
                """
                params["ip"] = ip
                params["is_vpn"] = is_vpn

            # Link Payment Card if present
            if card:
                cypher += """
                MERGE (c:PaymentCard {card_hash: $card})
                ON CREATE SET c.status = 'ACTIVE'
                MERGE (s)-[:SHARES_CARD]->(c)
                """
                params["card"] = card

            graph.query(cypher, params)
            row_count += 1

    duration = time.time() - t0
    nodes = graph.query("MATCH (n) RETURN count(n) AS cnt").result_set[0][0]
    edges = graph.query("MATCH ()-[r]->() RETURN count(r) AS cnt").result_set[0][0]

    print(f"[+] Successfully ingested {row_count} transaction records in {duration:.2f} seconds!")
    print(f"[+] Updated Graph '{graph_name}' Statistics:")
    print(f"    - Total Graph Nodes: {nodes}")
    print(f"    - Total Graph Edges: {edges}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Ingest custom banking data into FalkorDB for SybilShield")
    parser.add_argument("file", help="Path to banking ledger CSV file")
    parser.add_argument("--url", type=str, help="FalkorDB connection URL (or uses FALKORDB_URL from .env)")
    parser.add_argument("--host", type=str, help="FalkorDB host or IP")
    parser.add_argument("--port", type=int, help="FalkorDB port (default: 6379)")
    parser.add_argument("--graph", type=str, default="sybil_shield_demo", help="Target graph name")
    parser.add_argument("--clear", action="store_true", help="Clear existing graph before ingestion")

    args = parser.parse_args()

    ingest_banking_csv(
        csv_path=args.file,
        url=args.url,
        host=args.host,
        port=args.port,
        graph_name=args.graph,
        clear_existing=args.clear
    )


if __name__ == "__main__":
    main()
