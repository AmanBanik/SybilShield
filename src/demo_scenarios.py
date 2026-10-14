"""
The 10 Comprehensive Fraud & Benign Investigation Scenarios for SybilShield
Each scenario includes the target account, forensic trigger motivation,
expected verdict, topological explanation, and a ready-to-use Natural Language Prompt for Claude / AI clients.
"""

from typing import Dict, Any

SCENARIOS: Dict[str, Dict[str, Any]] = {
    "1": {
        "id": "1",
        "name": "Ghost Emulator Circular Laundering Ring",
        "target_account": "MULE_A",
        "severity": "CRITICAL",
        "trigger_reason": "High-velocity automated transfers ($15,000 threshold breached)",
        "expected_verdict": "CONFIRMED SYBIL NETWORK",
        "description": "A 4-node coordinated ring sharing a rooted emulator and datacenter VPN, laundering funds in a closed loop (A -> B -> C -> D -> A).",
        "claude_prompt": "We received an anomaly trigger for account 'MULE_A' sending $15,000. Investigate this account, expand its multi-hop connections for shared hardware or circular money routing, and execute a containment freeze if an organized ring is detected."
    },
    "2": {
        "id": "2",
        "name": "Stolen Credit Card Carding & Funnel Ring",
        "target_account": "MULE_E",
        "severity": "CRITICAL",
        "trigger_reason": "Card issuer alert on reported stolen card CARD_VISA_STOLEN_9901",
        "expected_verdict": "CONFIRMED SYBIL NETWORK",
        "description": "Two accounts share a compromised Visa card, funneling structured payments into a collector mule that off-ramps to an offshore crypto bridge.",
        "claude_prompt": "Issuer fraud alert: card 'CARD_VISA_STOLEN_9901' was reported stolen and used by account 'MULE_E'. Investigate MULE_E, check if other accounts share this card or route funds to high-risk cashout sinks, and isolate the network."
    },
    "3": {
        "id": "3",
        "name": "Android Emulator Bot Farm / Sybil Mesh",
        "target_account": "BOT_01",
        "severity": "HIGH",
        "trigger_reason": "Synthetic identity bot registration detected by risk engine",
        "expected_verdict": "CONFIRMED SYBIL NETWORK",
        "description": "Multiple bot accounts co-located on a NoxPlayer Android emulator farm and proxy network cycling micro-transfers between each other.",
        "claude_prompt": "Account 'BOT_01' is suspected of being part of a synthetic bot farm. Investigate its hardware fingerprint and IP transit links. If accomplice accounts share the same emulator instance, freeze the ring and blacklist the hardware."
    },
    "4": {
        "id": "4",
        "name": "Account Takeover (ATO) with Sudden Hardware Switch",
        "target_account": "VICTIM_DAVID",
        "severity": "HIGH",
        "trigger_reason": "Sudden device switch to Kali Linux over TOR exit node with $48k wire attempt",
        "expected_verdict": "CONFIRMED SYBIL NETWORK",
        "description": "A legitimate user account compromised by an attacker switching to a rooted device and proxy to drain $48,000 to an anonymous P2P escrow.",
        "claude_prompt": "Account 'VICTIM_DAVID' attempted a sudden $48,000 transfer. Investigate if David's login device or IP changed abruptly from his historical profile, verify downstream destination risk, and freeze the account to prevent unauthorized drain."
    },
    "5": {
        "id": "5",
        "name": "Dormant Sleeper Mule Rapid Reactivation",
        "target_account": "DORMANT_MULE_X",
        "severity": "HIGH",
        "trigger_reason": "Account inactive for 18 months suddenly attempting $32,000 transfer to Tornado OTC",
        "expected_verdict": "CONFIRMED SYBIL NETWORK",
        "description": "A sleeper mule account reactivated after long dormancy, using a stolen corporate Amex and routing $32,000 to an offshore mixer.",
        "claude_prompt": "Account 'DORMANT_MULE_X' was dormant for over a year and suddenly initiated a $32,000 transfer. Investigate its attached payment cards and downstream destination sinks. If connected to stolen cards or mixers, halt the transaction."
    },
    "6": {
        "id": "6",
        "name": "Merchant Bust-Out Collusion via Shill Buyers",
        "target_account": "SHILL_BUYER_01",
        "severity": "HIGH",
        "trigger_reason": "Repeated high-value payments ($18,500) to shell merchant on shared POS terminal",
        "expected_verdict": "CONFIRMED SYBIL NETWORK",
        "description": "Shill buyers sharing a rooted POS tablet funneling synthetic payments into a flagged shell merchant ('MERCHANT_SHILL_CORP').",
        "claude_prompt": "Investigate buyer account 'SHILL_BUYER_01'. Check its hardware association with merchant 'MERCHANT_SHILL_CORP' and other shill buyers. Disclose any collusion topology and mitigate."
    },
    "7": {
        "id": "7",
        "name": "Anchor Chokepoint Mule Detection",
        "target_account": "MULE_D",
        "severity": "HIGH",
        "trigger_reason": "High betweenness centrality detected on transfer ledger",
        "expected_verdict": "CONFIRMED SYBIL NETWORK",
        "description": "Evaluates MULE_D as an anchor node closing the loop back to MULE_A, proving how FalkorDB PageRank pinpoints critical laundering hubs.",
        "claude_prompt": "Run an investigation on account 'MULE_D'. Compute PageRank across the transfer network to determine if MULE_D is a central routing hub in an active laundering cycle."
    },
    "8": {
        "id": "8",
        "name": "Benign Retail Customer (Baseline Verification)",
        "target_account": "ACC_ALICE",
        "severity": "LOW / BENIGN",
        "trigger_reason": "Routine random compliance audit",
        "expected_verdict": "BENIGN TOPOLOGY",
        "description": "Standard individual user transacting from consumer iPhone and residential ISP with small retail coffee purchases. Must NOT be frozen.",
        "claude_prompt": "Audit customer account 'ACC_ALICE'. Investigate her devices, IPs, and transfer patterns. Confirm if her topology is benign or if there are any hidden Sybil indicators."
    },
    "9": {
        "id": "9",
        "name": "Family Household Shared iPad (Nuanced False Positive)",
        "target_account": "FAMILY_MOM",
        "severity": "LOW / BENIGN",
        "trigger_reason": "Two separate accounts detected sharing single device DEV_SHARED_FAMILY_IPAD",
        "expected_verdict": "BENIGN TOPOLOGY",
        "description": "Mother and son share an iPad and residential fiber IP for small allowance transfers. Demonstrates that SybilShield does NOT blindly flag legitimate family households.",
        "claude_prompt": "Risk alert: Accounts 'FAMILY_MOM' and 'FAMILY_SON' share a single iPad. Investigate their transfer history, amounts, and device type. Verify whether this is a legitimate household or an organized fraud ring."
    },
    "10": {
        "id": "10",
        "name": "Corporate CFO Payroll Wire ($250,000 Large Volume)",
        "target_account": "VIP_CORP_EXEC",
        "severity": "LOW / BENIGN",
        "trigger_reason": "Large wire transfer alert: $250,000 sent to Deloitte Payroll Escrow",
        "expected_verdict": "BENIGN TOPOLOGY",
        "description": "Corporate CFO sending quarterly payroll from an enterprise BitLocker laptop over dedicated corporate leased line. Proves high dollar amounts alone do not cause false freezes.",
        "claude_prompt": "Large transaction alert: 'VIP_CORP_EXEC' initiated a $250,000 transfer. Investigate if this is a legitimate corporate transaction or a laundering funnel. Do not freeze if the topology is clean and destination is a verified escrow."
    }
}
