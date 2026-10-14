import os
import time
import logging
from enum import Enum
from typing import Any, Dict, List, Optional
from src.db.connection import get_graph_client
from src.config import settings

logger = logging.getLogger(__name__)


class MitigationAction(str, Enum):
    FREEZE_ACCOUNTS = "FREEZE_ACCOUNTS"
    BLACKLIST_DEVICE = "BLACKLIST_DEVICE"
    BLACKLIST_CARD = "BLACKLIST_CARD"
    THROTTLE_VELOCITY = "THROTTLE_VELOCITY"
    DISPATCH_COMPLIANCE_ALERT = "DISPATCH_COMPLIANCE_ALERT"


class MitigationEngine:
    """Production-grade mitigation engine with granular, graph-native containment strategies.
    
    Easily extensible: add any new handler to execute_custom_action().
    """

    @classmethod
    def execute(
        cls,
        action: str,
        account_ids: Optional[List[str]] = None,
        device_ids: Optional[List[str]] = None,
        card_hashes: Optional[List[str]] = None,
        reason: str = "Automated SybilShield disruption",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Main dispatcher for mitigation strategies."""
        g = get_graph_client()
        ts = int(time.time())
        action_upper = action.upper()
        results: Dict[str, Any] = {
            "timestamp": ts,
            "requested_action": action_upper,
            "reason": reason,
            "applied": {}
        }

        # ----------------------------------------------------------------------
        # Strategy 1: Freeze Accounts (Ledger Locking + Audit Node)
        # ----------------------------------------------------------------------
        if account_ids and action_upper in [MitigationAction.FREEZE_ACCOUNTS, "FREEZE"]:
            query = """
            UNWIND $acc_ids AS target_id
            MATCH (a:Account {id: target_id})
            SET a.status = 'FROZEN',
                a.risk_score = 100,
                a.frozen_at = $ts
            CREATE (audit:AgentAudit {
                agent_id: $agent_id,
                action: 'FREEZE_ACCOUNT',
                reason: $reason,
                timestamp: $ts
            })
            CREATE (a)-[:MITIGATED_BY]->(audit)
            RETURN a.id AS frozen_id
            """
            res = g.query(query, {
                "acc_ids": account_ids,
                "agent_id": settings.agent_id,
                "reason": reason,
                "ts": ts
            })
            results["applied"]["frozen_accounts"] = [r[0] for r in res.result_set]

            # Auto-sever connected hardware emulators and compromised cards in the graph
            dev_block_query = """
            MATCH (a:Account)-[:USED_DEVICE]->(d:DeviceFingerprint)
            WHERE a.id IN $acc_ids
            SET d.status = 'BLACKLISTED',
                d.blacklisted_at = $ts
            RETURN DISTINCT d.device_id AS blocked_device
            """
            dev_res = g.query(dev_block_query, {"acc_ids": account_ids, "ts": ts})
            results["applied"]["blacklisted_devices"] = [r[0] for r in dev_res.result_set]

            card_block_query = """
            MATCH (a:Account)-[:SHARES_CARD]->(c:PaymentCard)
            WHERE a.id IN $acc_ids
            SET c.status = 'REVOKED',
                c.revoked_at = $ts
            RETURN DISTINCT c.card_hash AS revoked_card
            """
            card_res = g.query(card_block_query, {"acc_ids": account_ids, "ts": ts})
            results["applied"]["revoked_cards"] = [r[0] for r in card_res.result_set]

        # ----------------------------------------------------------------------
        # Strategy 2: Blacklist Physical Hardware (Device Fingerprints)
        # Prevents fraudsters from spinning up new accounts on the same device!
        # ----------------------------------------------------------------------
        if device_ids or action_upper == MitigationAction.BLACKLIST_DEVICE:
            target_devices = device_ids or []
            if not target_devices and account_ids:
                # Discover devices attached to the target accounts automatically
                dev_query = "MATCH (a:Account)-[:USED_DEVICE]->(d:DeviceFingerprint) WHERE a.id IN $acc_ids RETURN DISTINCT d.device_id"
                dev_res = g.query(dev_query, {"acc_ids": account_ids})
                target_devices = [r[0] for r in dev_res.result_set]

            if target_devices:
                block_dev_query = """
                UNWIND $dev_ids AS did
                MATCH (d:DeviceFingerprint {device_id: did})
                SET d.status = 'BLACKLISTED',
                    d.blacklisted_at = $ts,
                    d.blacklist_reason = $reason
                RETURN d.device_id AS blocked_device
                """
                res = g.query(block_dev_query, {"dev_ids": target_devices, "ts": ts, "reason": reason})
                results["applied"]["blacklisted_devices"] = [r[0] for r in res.result_set]

        # ----------------------------------------------------------------------
        # Strategy 3: Blacklist Payment Cards (Network-wide card blocking)
        # ----------------------------------------------------------------------
        if card_hashes or action_upper == MitigationAction.BLACKLIST_CARD:
            target_cards = card_hashes or []
            if not target_cards and account_ids:
                card_query = "MATCH (a:Account)-[:SHARES_CARD]->(c:PaymentCard) WHERE a.id IN $acc_ids RETURN DISTINCT c.card_hash"
                card_res = g.query(card_query, {"acc_ids": account_ids})
                target_cards = [r[0] for r in card_res.result_set]

            if target_cards:
                block_card_query = """
                UNWIND $chashes AS chash
                MATCH (c:PaymentCard {card_hash: chash})
                SET c.status = 'REVOKED',
                    c.revoked_at = $ts,
                    c.revocation_reason = $reason
                RETURN c.card_hash AS blocked_card
                """
                res = g.query(block_card_query, {"chashes": target_cards, "ts": ts, "reason": reason})
                results["applied"]["revoked_cards"] = [r[0] for r in res.result_set]

        # ----------------------------------------------------------------------
        # Strategy 4: Velocity Throttling (for borderline accomplices)
        # ----------------------------------------------------------------------
        if account_ids and action_upper == MitigationAction.THROTTLE_VELOCITY:
            throttle_query = """
            UNWIND $acc_ids AS target_id
            MATCH (a:Account {id: target_id})
            SET a.status = 'THROTTLED',
                a.daily_limit_usd = 100.0,
                a.throttled_at = $ts
            RETURN a.id AS throttled_id
            """
            res = g.query(throttle_query, {"acc_ids": account_ids, "ts": ts})
            results["applied"]["throttled_accounts"] = [r[0] for r in res.result_set]

        # ----------------------------------------------------------------------
        # Strategy 5: Webhook Notification (Mock/Production Webhook)
        # ----------------------------------------------------------------------
        webhook_url = os.getenv("COMPLIANCE_WEBHOOK_URL")
        results["applied"]["webhook_dispatched"] = cls._dispatch_webhook(webhook_url, results)

        results["success"] = True
        return results

    @staticmethod
    def _dispatch_webhook(url: Optional[str], payload: Dict[str, Any]) -> bool:
        """Dispatches an HTTP POST payload to core banking or Slack/PagerDuty webhook."""
        if not url:
            # Simulated webhook for local/hackathon environment
            logger.info("[MOCK WEBHOOK] Notification payload prepared for compliance.")
            return True
        try:
            import urllib.request
            req = urllib.request.Request(
                url,
                data=str(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status in [200, 201, 202]
        except Exception as e:
            logger.warning("Webhook dispatch failed: %s", e)
            return False
