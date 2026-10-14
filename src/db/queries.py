import time
from typing import Any, Dict, List, Optional
from src.db.connection import get_graph_client


class FraudGraphQueries:
    """Production Cypher query library for SybilShield fraud investigations."""

    @staticmethod
    def get_account_neighborhood(account_id: str) -> Optional[Dict[str, Any]]:
        """Inspects an account's immediate 1-hop profile and hardware/network infrastructure."""
        g = get_graph_client()
        query = """
        MATCH (a:Account {id: $acc_id})
        OPTIONAL MATCH (a)-[:USED_DEVICE]->(dev:DeviceFingerprint)
        OPTIONAL MATCH (a)-[:USED_IP]->(ip:IPAddress)
        OPTIONAL MATCH (a)-[:SHARES_CARD]->(card:PaymentCard)
        OPTIONAL MATCH (a)-[tx_out:TRANSFERRED]->(dest:Account)
        OPTIONAL MATCH (src:Account)-[tx_in:TRANSFERRED]->(a)
        RETURN a.id AS id,
               a.owner_name AS owner_name,
               a.status AS status,
               a.risk_score AS risk_score,
               collect(DISTINCT {id: dev.device_id, is_emulator: dev.is_emulator, os: dev.os}) AS devices,
               collect(DISTINCT {ip: ip.ip, is_vpn: ip.is_vpn, isp: ip.isp}) AS ips,
               collect(DISTINCT {card: card.card_hash, bank: card.issuing_bank}) AS cards,
               count(DISTINCT tx_out) AS tx_out_count,
               sum(DISTINCT tx_out.amount) AS total_sent,
               count(DISTINCT tx_in) AS tx_in_count,
               sum(DISTINCT tx_in.amount) AS total_received
        """
        res = g.query(query, {"acc_id": account_id})
        if not res.result_set:
            return None

        row = res.result_set[0]
        # Filter out empty/null entries from collect
        devices = [d for d in row[4] if d.get("id") is not None]
        ips = [i for i in row[5] if i.get("ip") is not None]
        cards = [c for c in row[6] if c.get("card") is not None]

        return {
            "account_id": row[0],
            "owner_name": row[1],
            "status": row[2],
            "risk_score": row[3],
            "devices": devices,
            "ips": ips,
            "cards": cards,
            "tx_out_count": row[7] or 0,
            "total_sent_usd": float(row[8] or 0.0),
            "tx_in_count": row[9] or 0,
            "total_received_usd": float(row[10] or 0.0),
        }

    @staticmethod
    def detect_sybil_ring(account_id: str, max_hops: int = 2) -> List[Dict[str, Any]]:
        """Finds accomplice accounts sharing device, IP, or card infrastructure."""
        g = get_graph_client()
        query = """
        MATCH (origin:Account {id: $acc_id})
        MATCH (origin)-[:USED_DEVICE|USED_IP|SHARES_CARD]-(vector)
        MATCH (accomplice:Account)-[:USED_DEVICE|USED_IP|SHARES_CARD]-(vector)
        WHERE accomplice <> origin
        RETURN accomplice.id AS accomplice_id,
               accomplice.owner_name AS owner_name,
               accomplice.status AS status,
               accomplice.risk_score AS risk_score,
               labels(vector)[0] AS shared_vector_type,
               count(DISTINCT vector) AS shared_links
        ORDER BY shared_links DESC
        LIMIT 25
        """
        res = g.query(query, {"acc_id": account_id})
        results = []
        for row in res.result_set:
            results.append({
                "accomplice_id": row[0],
                "owner_name": row[1],
                "status": row[2],
                "risk_score": row[3],
                "shared_vector_type": row[4],
                "shared_links": row[5]
            })
        return results

    @staticmethod
    def trace_fund_cycles(account_id: str, max_hops: int = 5) -> List[Dict[str, Any]]:
        """Detects circular money laundering cycles (e.g. A -> B -> C -> D -> A)."""
        g = get_graph_client()
        # Query cyclic paths using variable length traversal
        query = f"""
        MATCH path = (origin:Account {{id: $acc_id}})-[:TRANSFERRED*2..{max_hops}]->(origin)
        RETURN [n IN nodes(path) | n.id] AS cycle_accounts,
               length(path) AS hop_count,
               reduce(total = 0.0, tx IN relationships(path) | total + tx.amount) AS total_routed
        ORDER BY total_routed DESC
        LIMIT 5
        """
        res = g.query(query, {"acc_id": account_id})
        cycles = []
        for row in res.result_set:
            cycles.append({
                "cycle_path": row[0],
                "hop_count": row[1],
                "total_routed_usd": float(row[2])
            })
        return cycles

    @staticmethod
    def detect_cashout_flow(account_id: str) -> List[Dict[str, Any]]:
        """Detects if funds from the target account funnel into flagged or high-risk cashout sinks."""
        g = get_graph_client()
        query = """
        MATCH (origin:Account {id: $acc_id})-[:TRANSFERRED*1..3]->(sink:Account)
        WHERE sink.status = 'FLAGGED' OR sink.risk_score >= 80
        RETURN sink.id AS sink_id, sink.owner_name AS sink_name, sink.risk_score AS sink_risk
        """
        res = g.query(query, {"acc_id": account_id})
        return [{"sink_id": r[0], "sink_name": r[1], "sink_risk": r[2]} for r in res.result_set]

    @staticmethod
    def calculate_centrality(algorithm: str = "pagerank", top_k: int = 10) -> List[Dict[str, Any]]:
        """Calls FalkorDB native PageRank to determine top routing hubs in the transfer graph."""
        g = get_graph_client()
        try:
            query = """
            CALL algo.pageRank('Account', 'TRANSFERRED')
            YIELD node, score
            RETURN node.id AS account_id, node.owner_name AS owner_name, score
            ORDER BY score DESC
            LIMIT $top_k
            """
            res = g.query(query, {"top_k": top_k})
            results = []
            for row in res.result_set:
                results.append({
                    "account_id": row[0],
                    "owner_name": row[1],
                    "score": round(float(row[2]), 4)
                })
            return results
        except Exception:
            # Fallback in case graph topology has no transfer edges yet
            return []

    @staticmethod
    def execute_mitigation(action: str, account_ids: List[str], reason: str, agent_id: str = "SybilShield-Agent-01") -> Dict[str, Any]:
        """Freezes accounts, blacklists attached hardware/cards, and logs an immutable audit node in FalkorDB."""
        from src.mitigation.engine import MitigationEngine
        return MitigationEngine.execute(
            action=action,
            account_ids=account_ids,
            reason=reason
        )
