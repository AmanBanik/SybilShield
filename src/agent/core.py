import json
import logging
from typing import Any, Dict, List
from src.db.queries import FraudGraphQueries
from src.config import settings

logger = logging.getLogger(__name__)


class SybilShieldAgent:
    """Autonomous Financial Crime & Sybil Ring Disruption Agent.
    
    Executes a multi-hop graph decision loop on FalkorDB:
    1. 1-Hop Infrastructure Profiling
    2. Multi-Hop Sybil Cluster Expansion
    3. Circular Layering Cycle Detection
    4. Algorithmic Hub Centrality Analysis
    5. Autonomous Containment & SAR Reporting
    """

    def __init__(self, agent_id: str = settings.agent_id):
        self.agent_id = agent_id

    def investigate_prompt(self, prompt: str) -> Dict[str, Any]:
        """Parses a freeform natural language query, extracts mentioned targets, and executes the investigation."""
        from src.agent.nlp_resolver import QueryIntentResolver
        parsed = QueryIntentResolver.resolve_entities_from_text(prompt)
        target = parsed["primary_target"]
        
        reason = f"Natural Language Trigger: \"{prompt}\""
        res = self.investigate(target, trigger_reason=reason)
        res["nlp_parsed"] = parsed
        return res

    def investigate(self, target_account_id: str, trigger_reason: str = "Velocity Anomaly") -> Dict[str, Any]:
        """Runs an end-to-end autonomous forensic investigation on a flagged account."""
        steps_log: List[Dict[str, Any]] = []

        # ---------------------------------------------------------
        # Phase 1: 1-Hop Neighborhood Inspection
        # ---------------------------------------------------------
        profile = FraudGraphQueries.get_account_neighborhood(target_account_id)
        if not profile:
            return {
                "success": False,
                "error": f"Account '{target_account_id}' does not exist in FalkorDB graph."
            }

        emulator_detected = any(d.get("is_emulator", False) for d in profile["devices"])
        vpn_detected = any(i.get("is_vpn", False) for i in profile["ips"])
        
        steps_log.append({
            "phase": "1_HOP_INSPECTION",
            "action": "Queried direct account hardware and network linkages",
            "evidence": {
                "account_id": target_account_id,
                "emulator_flag": emulator_detected,
                "vpn_flag": vpn_detected,
                "devices_count": len(profile["devices"]),
                "ips_count": len(profile["ips"]),
                "cards_count": len(profile["cards"]),
                "sent_usd": profile["total_sent_usd"],
                "received_usd": profile["total_received_usd"]
            }
        })

        # ---------------------------------------------------------
        # Phase 2: Sybil Ring Expansion (Shared Physical Vectors)
        # ---------------------------------------------------------
        accomplices = FraudGraphQueries.detect_sybil_ring(target_account_id, max_hops=2)
        accomplice_ids = [a["accomplice_id"] for a in accomplices]
        full_cluster = list(set([target_account_id] + accomplice_ids))

        steps_log.append({
            "phase": "SYBIL_RING_EXPANSION",
            "action": "Traversed 2-hop shared device/IP/card subgraphs",
            "evidence": {
                "cluster_size": len(full_cluster),
                "accomplices": accomplices
            }
        })

        # ---------------------------------------------------------
        # Phase 3: Circular Laundering / Layering Loop Tracing
        # ---------------------------------------------------------
        cycles = FraudGraphQueries.trace_fund_cycles(target_account_id, max_hops=5)
        has_cycles = len(cycles) > 0
        total_cycle_volume = sum(c["total_routed_usd"] for c in cycles)

        steps_log.append({
            "phase": "CIRCULAR_CYCLE_TRACING",
            "action": "Evaluated transfer paths for closed cyclical loops",
            "evidence": {
                "cycles_found": len(cycles),
                "cycle_details": cycles,
                "total_cycle_volume_usd": total_cycle_volume
            }
        })

        # ---------------------------------------------------------
        # Phase 3b: Downstream Cash-Out Sink Funnel Analysis
        # ---------------------------------------------------------
        cashout_sinks = FraudGraphQueries.detect_cashout_flow(target_account_id)
        has_cashout_sinks = len(cashout_sinks) > 0
        shared_card_accomplices = [a for a in accomplices if a.get("shared_vector_type") == "PaymentCard"]

        steps_log.append({
            "phase": "CASHOUT_FLOW_ANALYSIS",
            "action": "Traced downstream transfer chains for high-risk/flagged destination sinks",
            "evidence": {
                "flagged_sinks_found": len(cashout_sinks),
                "sinks": cashout_sinks,
                "shared_cards_count": len(shared_card_accomplices)
            }
        })

        # ---------------------------------------------------------
        # Phase 4: FalkorDB PageRank Centrality Analysis
        # ---------------------------------------------------------
        centrality_ranking = FraudGraphQueries.calculate_centrality(algorithm="pagerank", top_k=10)
        top_mule_in_cluster = None
        for ranked in centrality_ranking:
            if ranked["account_id"] in full_cluster:
                top_mule_in_cluster = ranked
                break

        steps_log.append({
            "phase": "ALGORITHMIC_CENTRALITY",
            "action": "Executed FalkorDB PageRank to locate key routing hubs",
            "evidence": {
                "top_anchor_mule": top_mule_in_cluster,
                "overall_top_nodes": centrality_ranking[:3]
            }
        })

        # ---------------------------------------------------------
        # Phase 5: Autonomous Decision & Containment Action
        # ---------------------------------------------------------
        is_fraud_ring = False
        confidence = 0.0
        reasons = []

        if has_cycles:
            confidence += 0.50
            reasons.append(f"Confirmed circular laundering cycle ({cycles[0]['hop_count']} hops, ${total_cycle_volume:,.2f})")
        if emulator_detected:
            confidence += 0.25
            reasons.append("Operated via rooted/jailbroken emulator hardware or attacker tooling")
        if len(shared_card_accomplices) > 0:
            confidence += 0.35
            reasons.append(f"Payment card sharing between {len(shared_card_accomplices) + 1} accounts (synthetic carding ring)")
        elif len(accomplices) > 0:
            if emulator_detected or vpn_detected:
                confidence += 0.25
                reasons.append(f"Direct infrastructure sharing with {len(accomplices)} accomplice accounts on suspicious hardware/proxy")
            else:
                reasons.append(f"Legitimate household co-location with {len(accomplices)} family account (non-jailbroken consumer hardware)")
        if has_cashout_sinks:
            confidence += 0.40
            reasons.append(f"Direct/downstream fund routing into high-risk cashout sink '{cashout_sinks[0]['sink_name']}'")
            if len(profile.get("cards", [])) > 0:
                confidence += 0.35
                reasons.append(f"Payment card used to funnel unauthorized balance into flagged sink")
        if vpn_detected:
            confidence += 0.10
            reasons.append("Associated with datacenter VPN / TOR proxy IP")

        confidence = min(round(confidence, 2), 1.0)
        is_fraud_ring = confidence >= 0.70

        action_result = None
        if is_fraud_ring:
            action_reason = " | ".join(reasons)
            action_result = FraudGraphQueries.execute_mitigation(
                action="FREEZE",
                account_ids=full_cluster,
                reason=action_reason,
                agent_id=self.agent_id
            )
            final_status = "AUTONOMOUS_FREEZE_EXECUTED"
        else:
            final_status = "MONITORING_NO_CRITICAL_TOPOLOGY"

        # ---------------------------------------------------------
        # Assemble Executive Forensic Report
        # ---------------------------------------------------------
        sar_report = self._generate_sar_report(
            target_account_id=target_account_id,
            trigger_reason=trigger_reason,
            confidence=confidence,
            is_fraud_ring=is_fraud_ring,
            full_cluster=full_cluster,
            reasons=reasons,
            cycles=cycles,
            top_mule=top_mule_in_cluster,
            action_result=action_result
        )

        return {
            "success": True,
            "target_account": target_account_id,
            "confidence_score": confidence,
            "is_sybil_ring": is_fraud_ring,
            "cluster_members": full_cluster,
            "final_status": final_status,
            "steps": steps_log,
            "sar_report": sar_report
        }

    def _generate_sar_report(
        self,
        target_account_id: str,
        trigger_reason: str,
        confidence: float,
        is_fraud_ring: bool,
        full_cluster: List[str],
        reasons: List[str],
        cycles: List[Dict[str, Any]],
        top_mule: Any,
        action_result: Any
    ) -> str:
        """Formats a regulatory-grade Suspicious Activity Report (SAR)."""
        status_icon = "[CRITICAL ALERT] CONFIRMED SYBIL NETWORK" if is_fraud_ring else "[VERIFIED] BENIGN TOPOLOGY"
        top_mule_str = f"{top_mule['account_id']} (PageRank: {top_mule['score']})" if top_mule else "N/A"
        
        cycle_str = "None"
        if cycles:
            c = cycles[0]
            cycle_str = f"{' -> '.join(c['cycle_path'])} (Volume: ${c['total_routed_usd']:,.2f})"

        report = f"""
================================================================================
          SYBILSHIELD FORENSIC INCIDENT RESOLUTION REPORT
================================================================================
Incident Origin Target: {target_account_id}
Trigger Motivation:     {trigger_reason}
Verdict:                {status_icon}
Confidence Score:       {int(confidence * 100)}%
Target Cluster:         {', '.join(full_cluster)} (Size: {len(full_cluster)})
Key Routing Mule:       {top_mule_str}
Circular Loop Traced:   {cycle_str}

--------------------------------------------------------------------------------
Forensic Evidence Pillars:
"""
        for i, r in enumerate(reasons, 1):
            report += f"  {i}. {r}\n"

        if action_result:
            applied = action_result.get("applied", {})
            frozen_str = ", ".join(applied.get("frozen_accounts", [])) or "None"
            dev_str = ", ".join(applied.get("blacklisted_devices", [])) or "None"
            card_str = ", ".join(applied.get("revoked_cards", [])) or "None"
            report += f"""--------------------------------------------------------------------------------
Autonomous Mitigation Executed:
  - Action Requested:    {action_result.get('requested_action')}
  - Frozen Ledger:       {frozen_str}
  - Blacklisted Devices: {dev_str}
  - Revoked Cards:       {card_str}
  - Audit Node:          Immutable AgentAudit lineage created in FalkorDB
  - Webhook Dispatched:  {'Success' if applied.get('webhook_dispatched') else 'Simulated'}
"""
        report += "================================================================================\n"
        return report
