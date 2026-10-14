import re
from typing import Dict, Any, List, Optional
from src.db.connection import get_graph_client


class QueryIntentResolver:
    """Parses freeform natural language prompts to extract targets, risk cues, and requested actions."""

    @staticmethod
    def resolve_entities_from_text(prompt: str) -> Dict[str, Any]:
        """Extracts accounts, cards, devices, and actions from a user prompt using FalkorDB knowledge."""
        g = get_graph_client()
        prompt_upper = prompt.upper()

        # 1. Fetch all known node IDs and owners from FalkorDB
        accounts_res = g.query("MATCH (a:Account) RETURN a.id, a.owner_name").result_set
        cards_res = g.query("MATCH (c:PaymentCard) RETURN c.card_hash").result_set
        devices_res = g.query("MATCH (d:DeviceFingerprint) RETURN d.device_id").result_set

        known_cards = [r[0] for r in cards_res if r[0]]
        known_devices = [r[0] for r in devices_res if r[0]]

        detected_accounts: List[str] = []

        # Check scenario number mentions like 'scenario 2' or 'scenario 5'
        scenario_match = re.search(r'\bSCENARIO\s*(\d+)\b', prompt_upper)
        if scenario_match:
            sc_num = scenario_match.group(1)
            from src.demo_scenarios import SCENARIOS
            if sc_num in SCENARIOS:
                sc_acc = SCENARIOS[sc_num].get("target_account")
                if sc_acc:
                    detected_accounts.append(sc_acc)

        # 2. Find directly mentioned accounts or owners
        for r in accounts_res:
            acc_id = r[0]
            owner_name = r[1] if len(r) > 1 and r[1] else ""
            if acc_id and acc_id in prompt_upper:
                if acc_id not in detected_accounts:
                    detected_accounts.append(acc_id)
            elif owner_name and owner_name.upper() in prompt_upper:
                if acc_id not in detected_accounts:
                    detected_accounts.append(acc_id)
            elif owner_name:
                first_name = owner_name.split()[0].upper()
                if len(first_name) >= 4 and re.search(r'\b' + re.escape(first_name) + r'\b', prompt_upper):
                    if acc_id not in detected_accounts:
                        detected_accounts.append(acc_id)

        detected_cards = [c for c in known_cards if c in prompt_upper]
        detected_devices = [d for d in known_devices if d in prompt_upper]

        # 3. If a card is mentioned without an account, look up linked accounts in FalkorDB
        for card_hash in detected_cards:
            res = g.query("MATCH (a:Account)-[:SHARES_CARD]->(c:PaymentCard {card_hash: $c}) RETURN a.id", {"c": card_hash})
            for r in res.result_set:
                if r[0] not in detected_accounts:
                    detected_accounts.append(r[0])

        # 4. If a device is mentioned without an account, look up linked accounts in FalkorDB
        for dev_id in detected_devices:
            res = g.query("MATCH (a:Account)-[:USED_DEVICE]->(d:DeviceFingerprint {device_id: $d}) RETURN a.id", {"d": dev_id})
            for r in res.result_set:
                if r[0] not in detected_accounts:
                    detected_accounts.append(r[0])

        # 5. Fallback: regex token search for patterns like MULE_*, ACC_*, BOT_*, etc.
        if not detected_accounts:
            regex_matches = re.findall(r'\b(MULE_[A-Z0-9]+|ACC_[A-Z0-9_]+|BOT_\d+|VICTIM_[A-Z]+|FAMILY_[A-Z]+|VIP_[A-Z]+|SHILL_[A-Z0-9_]+|DORMANT_[A-Z0-9_]+)\b', prompt_upper)
            for m in regex_matches:
                if m not in detected_accounts:
                    detected_accounts.append(m)

        # 6. If still no account detected, pick highest risk or top PageRank account in the network
        is_generic_sweep = False
        if not detected_accounts:
            is_generic_sweep = True
            top_risk_res = g.query("MATCH (a:Account) RETURN a.id ORDER BY a.risk_score DESC LIMIT 1").result_set
            if top_risk_res:
                detected_accounts.append(top_risk_res[0][0])

        primary_target = detected_accounts[0] if detected_accounts else "MULE_A"

        # Action hints
        wants_freeze = any(w in prompt_upper for w in ["FREEZE", "BLOCK", "CONTAIN", "ISOLATE", "HALT", "STOP"])

        return {
            "primary_target": primary_target,
            "all_detected_accounts": detected_accounts,
            "detected_cards": detected_cards,
            "detected_devices": detected_devices,
            "wants_freeze": wants_freeze,
            "is_generic_sweep": is_generic_sweep,
            "original_prompt": prompt
        }
