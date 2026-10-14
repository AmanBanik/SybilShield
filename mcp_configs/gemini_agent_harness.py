import os
import sys
import json
import argparse
from typing import Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.demo_scenarios import SCENARIOS
from src.mcp.server import (
    investigate_account,
    detect_sybil_ring,
    trace_fund_cycles,
    calculate_ring_centrality,
    execute_mitigation,
    blacklist_compromised_instrument
)


# Mapping of registered MCP tools for direct execution
AVAILABLE_TOOLS = {
    "investigate_account": investigate_account,
    "detect_sybil_ring": detect_sybil_ring,
    "trace_fund_cycles": trace_fund_cycles,
    "calculate_ring_centrality": calculate_ring_centrality,
    "execute_mitigation": execute_mitigation,
    "blacklist_compromised_instrument": blacklist_compromised_instrument
}


def run_llm_harness_investigation(scenario_key: str):
    """Executes a simulated multi-turn tool-calling loop using the scenario prompt."""
    scenario = SCENARIOS.get(scenario_key)
    if not scenario:
        print(f"[-] Invalid scenario ID: {scenario_key}")
        return

    print("\n" + "="*70)
    print(f" [AI AGENT HARNESS] EXECUTING SCENARIO {scenario_key}")
    print("="*70)
    print(f"[*] Scenario Name: {scenario['name']}")
    print(f"[*] Natural Language Prompt:")
    print(f"    \"{scenario['claude_prompt']}\"")
    print("-"*70)

    target_acc = scenario["target_account"]

    # Turn 1: LLM selects investigate_account
    print("\n[Turn 1] LLM Action -> Calling Tool: investigate_account()")
    turn1_result = investigate_account(target_acc)
    print(f"  Tool Output: Found {len(turn1_result.get('devices', []))} devices, {len(turn1_result.get('ips', []))} IPs, {len(turn1_result.get('cards', []))} cards.")

    # Turn 2: LLM evaluates infrastructure and calls detect_sybil_ring
    print("\n[Turn 2] LLM Action -> Calling Tool: detect_sybil_ring()")
    turn2_result = detect_sybil_ring(target_acc, max_hops=2)
    accomplice_ids = [a["accomplice_id"] for a in turn2_result]
    print(f"  Tool Output: Found {len(accomplice_ids)} accomplice accounts sharing infrastructure.")

    # Turn 3: LLM checks for circular layering cycles
    print("\n[Turn 3] LLM Action -> Calling Tool: trace_fund_cycles()")
    turn3_result = trace_fund_cycles(target_acc, max_hops=5)
    has_cycle = len(turn3_result) > 0
    if has_cycle:
        c = turn3_result[0]
        print(f"  Tool Output: Cycle confirmed: {' -> '.join(c['cycle_path'])} (Volume: ${c['total_routed_usd']:,.2f})")
    else:
        print("  Tool Output: No circular fund flow detected.")

    # Turn 4: LLM checks PageRank centrality
    print("\n[Turn 4] LLM Action -> Calling Tool: calculate_ring_centrality()")
    turn4_result = calculate_ring_centrality(top_k=5)
    print(f"  Tool Output: Top routing node: {turn4_result[0]['account_id'] if turn4_result else 'None'}")

    # Turn 5: LLM Decision & Mitigation
    print("\n[Turn 5] LLM Action -> Evaluating Topological Evidence & Deciding Action")
    is_fraud = has_cycle or (len(turn2_result) > 0 and any(d.get("is_emulator") for d in turn1_result.get("devices", []))) or any(c.get("is_vpn") for c in turn1_result.get("ips", []))
    
    if is_fraud:
        targets_to_freeze = list(set([target_acc] + accomplice_ids))
        print(f"  Verdict: CRITICAL FRAUD RING DETECTED. Freezing {targets_to_freeze}")
        mitigation_res = execute_mitigation(
            action="FREEZE",
            account_ids=targets_to_freeze,
            reason=f"Automated MCP Disruption: {scenario['trigger_reason']}"
        )
        print("  Mitigation Result:", json.dumps(mitigation_res.get("applied", {}), indent=2))
    else:
        print(f"  Verdict: BENIGN TOPOLOGY. Account '{target_acc}' verified safe. No containment action required.")

    print("\n" + "="*70)
    print(" [HARNESS COMPLETE] Multi-Turn Tool Loop Concluded.")
    print("="*70 + "\n")


def run_prompt_harness_investigation(prompt: str):
    """Executes a multi-turn tool-calling loop using a freeform natural language query."""
    from src.agent.nlp_resolver import QueryIntentResolver
    parsed = QueryIntentResolver.resolve_entities_from_text(prompt)
    target_acc = parsed["primary_target"]

    print("\n" + "="*70)
    print(" [AI AGENT HARNESS] EXECUTING FREEFORM NATURAL LANGUAGE QUERY")
    print("="*70)
    print(f"[*] Input Prompt: \"{prompt}\"")
    print(f"[*] Resolved Target Account: {target_acc}")
    if parsed.get("detected_cards"):
        print(f"[*] Extracted Card Hash: {parsed['detected_cards']}")
    if parsed.get("detected_devices"):
        print(f"[*] Extracted Device ID: {parsed['detected_devices']}")
    print("-"*70)

    # Turn 1: LLM selects investigate_account
    print("\n[Turn 1] LLM Action -> Calling Tool: investigate_account()")
    turn1_result = investigate_account(target_acc)
    print(f"  Tool Output: Found {len(turn1_result.get('devices', []))} devices, {len(turn1_result.get('ips', []))} IPs, {len(turn1_result.get('cards', []))} cards.")

    # Turn 2: LLM evaluates infrastructure and calls detect_sybil_ring
    print("\n[Turn 2] LLM Action -> Calling Tool: detect_sybil_ring()")
    turn2_result = detect_sybil_ring(target_acc, max_hops=2)
    accomplice_ids = [a["accomplice_id"] for a in turn2_result]
    print(f"  Tool Output: Found {len(accomplice_ids)} accomplice accounts sharing infrastructure.")

    # Turn 3: LLM checks for circular layering cycles
    print("\n[Turn 3] LLM Action -> Calling Tool: trace_fund_cycles()")
    turn3_result = trace_fund_cycles(target_acc, max_hops=5)
    has_cycle = len(turn3_result) > 0
    if has_cycle:
        c = turn3_result[0]
        print(f"  Tool Output: Cycle confirmed: {' -> '.join(c['cycle_path'])} (Volume: ${c['total_routed_usd']:,.2f})")
    else:
        print("  Tool Output: No circular fund flow detected.")

    # Turn 4: LLM checks PageRank centrality
    print("\n[Turn 4] LLM Action -> Calling Tool: calculate_ring_centrality()")
    turn4_result = calculate_ring_centrality(top_k=5)
    print(f"  Tool Output: Top routing node: {turn4_result[0]['account_id'] if turn4_result else 'None'}")

    # Turn 5: LLM Decision & Mitigation
    print("\n[Turn 5] LLM Action -> Evaluating Topological Evidence & Deciding Action")
    is_fraud = has_cycle or (len(turn2_result) > 0 and any(d.get("is_emulator") for d in turn1_result.get("devices", []))) or any(c.get("is_vpn") for c in turn1_result.get("ips", []))
    
    if is_fraud:
        targets_to_freeze = list(set([target_acc] + accomplice_ids))
        print(f"  Verdict: CRITICAL FRAUD RING DETECTED. Freezing {targets_to_freeze}")
        mitigation_res = execute_mitigation(
            action="FREEZE",
            account_ids=targets_to_freeze,
            reason=f"Natural Language Trigger: {prompt}"
        )
        print("  Mitigation Result:", json.dumps(mitigation_res.get("applied", {}), indent=2))
    else:
        print(f"  Verdict: BENIGN TOPOLOGY. Account '{target_acc}' verified safe. No containment action required.")

    print("\n" + "="*70)
    print(" [HARNESS COMPLETE] Multi-Turn Tool Loop Concluded.")
    print("="*70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Agent MCP Harness Runner")
    parser.add_argument("--scenario", "-s", help="Scenario ID (1-10)")
    parser.add_argument("--prompt", "-p", help="Freeform natural language prompt to investigate")
    args = parser.parse_args()

    if args.prompt:
        run_prompt_harness_investigation(args.prompt)
    else:
        sc_id = args.scenario or "1"
        run_llm_harness_investigation(sc_id)
