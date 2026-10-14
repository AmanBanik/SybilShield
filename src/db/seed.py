"""
Synthetic Fraud & Financial Topology Generator for SybilShield
Populates FalkorDB with 10 distinct, realistic situations:
- 7 Advanced Fraud & Disruption Topologies (Circular, Botnets, Stolen Cards, ATO, Merchant Collusion, Dormant Mules)
- 3 Legitimate & Complex Edge Cases (Everyday retail, Shared Family iPad, Corporate High-Value Wire)
"""

import sys
from typing import Optional
from src.config import settings
from src.db.connection import get_falkordb_client


def seed_synthetic_fraud_network(
    url: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    graph_name: str = settings.falkordb_graph
):
    target_url = url or settings.falkordb_url
    if target_url:
        print(f"[*] Connecting to FalkorDB via Cloud URL...")
        db = get_falkordb_client(url=target_url)
    elif host and port:
        print(f"[*] Connecting to FalkorDB at {host}:{port}...")
        from falkordb import FalkorDB
        db = FalkorDB(host=host, port=port)
    else:
        print(f"[*] Connecting to FalkorDB ({settings.falkordb_host}:{settings.falkordb_port})...")
        db = get_falkordb_client()
    
    try:
        db.select_graph(graph_name).delete()
        print(f"[*] Cleared previous '{graph_name}' graph.")
    except Exception:
        pass
    
    graph = db.select_graph(graph_name)
    print(f"[*] Seeding expanded 10-scenario network into graph '{graph_name}'...")

    # 1. Performance Indexes
    indexes = [
        "CREATE INDEX FOR (a:Account) ON (a.id)",
        "CREATE INDEX FOR (d:DeviceFingerprint) ON (d.device_id)",
        "CREATE INDEX FOR (i:IPAddress) ON (i.ip)",
        "CREATE INDEX FOR (c:PaymentCard) ON (c.card_hash)"
    ]
    for idx_query in indexes:
        try:
            graph.query(idx_query)
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # Cluster 1: Legitimate Retail Baseline (Scenario 8: ACC_ALICE)
    # --------------------------------------------------------------------------
    c1_cypher = """
    CREATE (alice:Account {id: 'ACC_ALICE', owner_name: 'Alice Smith', status: 'ACTIVE', risk_score: 5, created_at: 1700000000})
    CREATE (bob:Account {id: 'ACC_BOB', owner_name: 'Bob Jones', status: 'ACTIVE', risk_score: 8, created_at: 1700000000})
    CREATE (coffee_shop:Account {id: 'ACC_COFFEE', owner_name: 'Downtown Coffee LLC', status: 'MERCHANT', risk_score: 0, created_at: 1690000000})
    
    CREATE (dev_alice:DeviceFingerprint {device_id: 'DEV_ALICE_IPHONE', os: 'iOS 18', is_emulator: false})
    CREATE (dev_bob:DeviceFingerprint {device_id: 'DEV_BOB_PIXEL', os: 'Android 15', is_emulator: false})
    CREATE (ip_home1:IPAddress {ip: '203.0.113.10', isp: 'Comcast Consumer Fiber', is_vpn: false})
    CREATE (ip_home2:IPAddress {ip: '203.0.113.25', isp: 'Verizon Fios', is_vpn: false})
    
    CREATE (alice)-[:USED_DEVICE {last_seen: 1710000000}]->(dev_alice)
    CREATE (alice)-[:USED_IP {last_seen: 1710000000}]->(ip_home1)
    CREATE (bob)-[:USED_DEVICE {last_seen: 1710000000}]->(dev_bob)
    CREATE (bob)-[:USED_IP {last_seen: 1710000000}]->(ip_home2)
    
    CREATE (alice)-[:TRANSFERRED {amount: 45.50, timestamp: 1710001000, tx_id: 'TX_L1'}]->(coffee_shop)
    CREATE (bob)-[:TRANSFERRED {amount: 120.00, timestamp: 1710002000, tx_id: 'TX_L2'}]->(coffee_shop)
    CREATE (alice)-[:TRANSFERRED {amount: 25.00, timestamp: 1710003000, tx_id: 'TX_L3'}]->(bob)
    """
    graph.query(c1_cypher)

    # --------------------------------------------------------------------------
    # Cluster 2: Ghost Emulator Circular Layering Ring (Scenario 1: MULE_A, Scenario 7: MULE_D)
    # --------------------------------------------------------------------------
    c2_cypher = """
    CREATE (mule_a:Account {id: 'MULE_A', owner_name: 'John Doe I', status: 'ACTIVE', risk_score: 45, created_at: 1712000000})
    CREATE (mule_b:Account {id: 'MULE_B', owner_name: 'John Doe II', status: 'ACTIVE', risk_score: 50, created_at: 1712000100})
    CREATE (mule_c:Account {id: 'MULE_C', owner_name: 'Jane Roe I', status: 'ACTIVE', risk_score: 55, created_at: 1712000200})
    CREATE (mule_d:Account {id: 'MULE_D', owner_name: 'Jane Roe II', status: 'ACTIVE', risk_score: 60, created_at: 1712000300})
    
    CREATE (dev_ghost:DeviceFingerprint {device_id: 'DEV_GHOST_EMULATOR_88', os: 'Linux Rooted VM', is_emulator: true})
    CREATE (ip_tor:IPAddress {ip: '198.51.100.99', isp: 'Datacenter VPN M247', is_vpn: true})
    
    CREATE (mule_a)-[:USED_DEVICE {last_seen: 1712001000}]->(dev_ghost)
    CREATE (mule_b)-[:USED_DEVICE {last_seen: 1712001100}]->(dev_ghost)
    CREATE (mule_c)-[:USED_DEVICE {last_seen: 1712001200}]->(dev_ghost)
    CREATE (mule_c)-[:USED_IP {last_seen: 1712001300}]->(ip_tor)
    CREATE (mule_d)-[:USED_IP {last_seen: 1712001400}]->(ip_tor)
    
    CREATE (mule_a)-[:TRANSFERRED {amount: 15000.00, timestamp: 1712010000, tx_id: 'TX_RING1_1'}]->(mule_b)
    CREATE (mule_b)-[:TRANSFERRED {amount: 14500.00, timestamp: 1712013600, tx_id: 'TX_RING1_2'}]->(mule_c)
    CREATE (mule_c)-[:TRANSFERRED {amount: 14200.00, timestamp: 1712017200, tx_id: 'TX_RING1_3'}]->(mule_d)
    CREATE (mule_d)-[:TRANSFERRED {amount: 13800.00, timestamp: 1712020800, tx_id: 'TX_RING1_4'}]->(mule_a)
    """
    graph.query(c2_cypher)

    # --------------------------------------------------------------------------
    # Cluster 3: Stolen Card Structuring Funnel (Scenario 2: MULE_E)
    # --------------------------------------------------------------------------
    c3_cypher = """
    CREATE (victim_card:PaymentCard {card_hash: 'CARD_VISA_STOLEN_9901', issuing_bank: 'Metro Bank NYC'})
    CREATE (mule_e:Account {id: 'MULE_E', owner_name: 'Arthur Mule', status: 'ACTIVE', risk_score: 70, created_at: 1713000000})
    CREATE (mule_f:Account {id: 'MULE_F', owner_name: 'Brenda Mule', status: 'ACTIVE', risk_score: 65, created_at: 1713000100})
    CREATE (mule_g:Account {id: 'MULE_G', owner_name: 'Carl Mule', status: 'ACTIVE', risk_score: 65, created_at: 1713000200})
    CREATE (cashout_crypto:Account {id: 'ACC_CASHOUT_CRYPTO', owner_name: 'Offshore Crypto Bridge LLC', status: 'FLAGGED', risk_score: 95, created_at: 1705000000})
    
    CREATE (mule_e)-[:SHARES_CARD]->(victim_card)
    CREATE (mule_f)-[:SHARES_CARD]->(victim_card)
    
    CREATE (mule_e)-[:TRANSFERRED {amount: 9500.00, timestamp: 1713001000, tx_id: 'TX_RING2_1'}]->(mule_g)
    CREATE (mule_f)-[:TRANSFERRED {amount: 9800.00, timestamp: 1713001500, tx_id: 'TX_RING2_2'}]->(mule_g)
    CREATE (mule_g)-[:TRANSFERRED {amount: 19000.00, timestamp: 1713005000, tx_id: 'TX_RING2_3'}]->(cashout_crypto)
    """
    graph.query(c3_cypher)

    # --------------------------------------------------------------------------
    # Cluster 4: Automated Android Emulator Botnet (Scenario 3: BOT_01)
    # --------------------------------------------------------------------------
    c4_cypher = """
    CREATE (bot_1:Account {id: 'BOT_01', owner_name: 'Synthetic Bot Alpha', status: 'ACTIVE', risk_score: 60, created_at: 1714000000})
    CREATE (bot_2:Account {id: 'BOT_02', owner_name: 'Synthetic Bot Beta', status: 'ACTIVE', risk_score: 60, created_at: 1714000000})
    CREATE (bot_3:Account {id: 'BOT_03', owner_name: 'Synthetic Bot Gamma', status: 'ACTIVE', risk_score: 60, created_at: 1714000000})
    
    CREATE (dev_nox:DeviceFingerprint {device_id: 'DEV_NOX_EMULATOR_FARM', os: 'NoxPlayer Android 9 Rooted', is_emulator: true})
    CREATE (ip_bot_vpn:IPAddress {ip: '185.220.101.5', isp: 'Hydra Proxy Network', is_vpn: true})
    
    CREATE (bot_1)-[:USED_DEVICE]->(dev_nox)
    CREATE (bot_2)-[:USED_DEVICE]->(dev_nox)
    CREATE (bot_3)-[:USED_DEVICE]->(dev_nox)
    CREATE (bot_1)-[:USED_IP]->(ip_bot_vpn)
    CREATE (bot_2)-[:USED_IP]->(ip_bot_vpn)
    CREATE (bot_3)-[:USED_IP]->(ip_bot_vpn)
    
    CREATE (bot_1)-[:TRANSFERRED {amount: 2500.00, timestamp: 1714001000, tx_id: 'TX_BOT1'}]->(bot_2)
    CREATE (bot_2)-[:TRANSFERRED {amount: 2450.00, timestamp: 1714002000, tx_id: 'TX_BOT2'}]->(bot_3)
    CREATE (bot_3)-[:TRANSFERRED {amount: 2400.00, timestamp: 1714003000, tx_id: 'TX_BOT3'}]->(bot_1)
    """
    graph.query(c4_cypher)

    # --------------------------------------------------------------------------
    # Cluster 5: Account Takeover (ATO) Incident (Scenario 4: VICTIM_DAVID)
    # --------------------------------------------------------------------------
    c5_cypher = """
    CREATE (david:Account {id: 'VICTIM_DAVID', owner_name: 'David Miller', status: 'ACTIVE', risk_score: 20, created_at: 1680000000})
    CREATE (hacker_sink:Account {id: 'HACKER_CASHOUT_POCKET', owner_name: 'Anonymous P2P Escrow', status: 'FLAGGED', risk_score: 99, created_at: 1714500000})
    
    CREATE (dev_david_old:DeviceFingerprint {device_id: 'DEV_DAVID_MACBOOK', os: 'macOS Sonoma', is_emulator: false})
    CREATE (dev_hacker:DeviceFingerprint {device_id: 'DEV_KALI_ATTACKER_99', os: 'Kali Linux Rolling', is_emulator: true})
    CREATE (ip_tor_exit:IPAddress {ip: '176.10.99.200', isp: 'TOR Exit Node Zurich', is_vpn: true})
    
    CREATE (david)-[:USED_DEVICE {last_seen: 1714000000}]->(dev_david_old)
    CREATE (david)-[:USED_DEVICE {last_seen: 1714501000}]->(dev_hacker)
    CREATE (david)-[:USED_IP {last_seen: 1714501000}]->(ip_tor_exit)
    
    CREATE (david)-[:TRANSFERRED {amount: 48000.00, timestamp: 1714501500, tx_id: 'TX_ATO_DRAIN'}]->(hacker_sink)
    """
    graph.query(c5_cypher)

    # --------------------------------------------------------------------------
    # Cluster 6: Sleeper Dormant Mule Reactivation (Scenario 5: DORMANT_MULE_X)
    # --------------------------------------------------------------------------
    c6_cypher = """
    CREATE (dormant_mule:Account {id: 'DORMANT_MULE_X', owner_name: 'Victor Vance', status: 'ACTIVE', risk_score: 30, created_at: 1670000000})
    CREATE (mixer_sink:Account {id: 'OFFSHORE_MIXER_Y', owner_name: 'Tornado OTC Liquidity', status: 'FLAGGED', risk_score: 98, created_at: 1710000000})
    CREATE (card_stolen_sub:PaymentCard {card_hash: 'CARD_AMEX_CORP_STOLEN_440', issuing_bank: 'Amex Business'})
    
    CREATE (dormant_mule)-[:SHARES_CARD]->(card_stolen_sub)
    CREATE (dormant_mule)-[:TRANSFERRED {amount: 32000.00, timestamp: 1714600000, tx_id: 'TX_DORMANT_DRAIN'}]->(mixer_sink)
    """
    graph.query(c6_cypher)

    # --------------------------------------------------------------------------
    # Cluster 7: Merchant Bust-Out Collusion (Scenario 6: MERCHANT_SHILL_CORP)
    # --------------------------------------------------------------------------
    c7_cypher = """
    CREATE (fake_merchant:Account {id: 'MERCHANT_SHILL_CORP', owner_name: 'Prestige Diamond Exchange Shell', status: 'FLAGGED', risk_score: 88, created_at: 1713000000})
    CREATE (shill_1:Account {id: 'SHILL_BUYER_01', owner_name: 'Liam Vance', status: 'ACTIVE', risk_score: 55, created_at: 1713500000})
    CREATE (shill_2:Account {id: 'SHILL_BUYER_02', owner_name: 'Noah Vance', status: 'ACTIVE', risk_score: 55, created_at: 1713500000})
    
    CREATE (dev_shared_shill:DeviceFingerprint {device_id: 'DEV_SHARED_TABLET_POS', os: 'Android 14 POS Rooted', is_emulator: true})
    CREATE (shill_1)-[:USED_DEVICE]->(dev_shared_shill)
    CREATE (shill_2)-[:USED_DEVICE]->(dev_shared_shill)
    
    CREATE (shill_1)-[:TRANSFERRED {amount: 18500.00, timestamp: 1714601000, tx_id: 'TX_SHILL_1'}]->(fake_merchant)
    CREATE (shill_2)-[:TRANSFERRED {amount: 19200.00, timestamp: 1714602000, tx_id: 'TX_SHILL_2'}]->(fake_merchant)
    """
    graph.query(c7_cypher)

    # --------------------------------------------------------------------------
    # Cluster 8: Shared Family Household iPad (Scenario 9: FAMILY_MOM) - False Positive
    # --------------------------------------------------------------------------
    c8_cypher = """
    CREATE (mom:Account {id: 'FAMILY_MOM', owner_name: 'Sarah Connor', status: 'ACTIVE', risk_score: 4, created_at: 1690000000})
    CREATE (son:Account {id: 'FAMILY_SON', owner_name: 'John Connor', status: 'ACTIVE', risk_score: 6, created_at: 1705000000})
    
    CREATE (shared_ipad:DeviceFingerprint {device_id: 'DEV_SHARED_FAMILY_IPAD', os: 'iPadOS 18 Unjailbroken', is_emulator: false})
    CREATE (home_fiber:IPAddress {ip: '73.189.42.11', isp: 'AT&T Consumer Residential Fiber', is_vpn: false})
    
    CREATE (mom)-[:USED_DEVICE]->(shared_ipad)
    CREATE (son)-[:USED_DEVICE]->(shared_ipad)
    CREATE (mom)-[:USED_IP]->(home_fiber)
    CREATE (son)-[:USED_IP]->(home_fiber)
    
    CREATE (mom)-[:TRANSFERRED {amount: 50.00, timestamp: 1714700000, tx_id: 'TX_ALLOWANCE'}]->(son)
    """
    graph.query(c8_cypher)

    # --------------------------------------------------------------------------
    # Cluster 9: Corporate High-Value Payroll Wire (Scenario 10: VIP_CORP_EXEC) - False Positive
    # --------------------------------------------------------------------------
    c9_cypher = """
    CREATE (vip_exec:Account {id: 'VIP_CORP_EXEC', owner_name: 'Elena Rostova (CFO)', status: 'ACTIVE', risk_score: 2, created_at: 1660000000})
    CREATE (corp_escrow:Account {id: 'CORP_PAYROLL_ESCROW', owner_name: 'Deloitte Global Payroll Escrow', status: 'MERCHANT', risk_score: 0, created_at: 1650000000})
    
    CREATE (dev_exec_thinkpad:DeviceFingerprint {device_id: 'DEV_CORP_THINKPAD_YOGA', os: 'Windows 11 Enterprise BitLocker', is_emulator: false})
    CREATE (ip_corp_hq:IPAddress {ip: '140.82.112.4', isp: 'Corporate Dedicated Leased Line', is_vpn: false})
    
    CREATE (vip_exec)-[:USED_DEVICE]->(dev_exec_thinkpad)
    CREATE (vip_exec)-[:USED_IP]->(ip_corp_hq)
    
    CREATE (vip_exec)-[:TRANSFERRED {amount: 250000.00, timestamp: 1714800000, tx_id: 'TX_CORP_PAYROLL'}]->(corp_escrow)
    """
    graph.query(c9_cypher)

    # Count nodes and edges
    node_count = graph.query("MATCH (n) RETURN count(n) AS cnt").result_set[0][0]
    edge_count = graph.query("MATCH ()-[r]->() RETURN count(r) AS cnt").result_set[0][0]

    print("\n" + "="*60)
    print(" [SEED COMPLETE] 10 Scenarios Synthesized into FalkorDB!")
    print("="*60)
    print(f" -> Graph Name: {graph_name}")
    print(f" -> Total Nodes: {node_count}")
    print(f" -> Total Edges: {edge_count}")
    print(f" -> FalkorDB Browser: http://localhost:3000")
    print("="*60 + "\n")


if __name__ == "__main__":
    seed_synthetic_fraud_network()
