import json
import time
import streamlit as st
import streamlit.components.v1 as components

from src.config import settings
from src.db.connection import get_graph_client, test_db_connection
from src.db.seed import seed_synthetic_fraud_network
from src.agent.core import SybilShieldAgent
from src.demo_scenarios import SCENARIOS

# Page Configuration
st.set_page_config(
    page_title="SybilShield | Autonomous Financial Graph Defense",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Fintech Dark Cybersecurity Theme)
st.markdown("""
<style>
    .main { background-color: #0b0f19; color: #f8fafc; }
    .stMetric { background-color: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 14px; }
    div[data-testid="stExpander"] { background-color: #111827; border: 1px solid #1f2937; border-radius: 8px; margin-bottom: 8px; }
    .badge-critical { background-color: #dc2626; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 13px; }
    .badge-high { background-color: #ea580c; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 13px; }
    .badge-safe { background-color: #059669; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 13px; }
    .prompt-box { background-color: #1e293b; border-left: 4px solid #38bdf8; padding: 10px 14px; border-radius: 4px; font-family: monospace; font-size: 12px; }
    .nlp-pill { background-color: #1e293b; border: 1px solid #38bdf8; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; }
</style>
""", unsafe_allow_html=True)


def get_graph_stats():
    """Fetches real-time node and edge counts from FalkorDB."""
    try:
        g = get_graph_client()
        t0 = time.time()
        nodes = g.query("MATCH (n) RETURN count(n) AS cnt").result_set[0][0]
        edges = g.query("MATCH ()-[r]->() RETURN count(r) AS cnt").result_set[0][0]
        frozen = g.query("MATCH (a:Account {status: 'FROZEN'}) RETURN count(a) AS cnt").result_set[0][0]
        latency_ms = (time.time() - t0) * 1000
        return {"online": True, "nodes": nodes, "edges": edges, "frozen": frozen, "latency_ms": latency_ms}
    except Exception:
        return {"online": False, "nodes": 0, "edges": 0, "frozen": 0, "latency_ms": 0}


def render_graph_canvas():
    """Generates an interactive force-directed graph canvas using vis-network embedded in Streamlit."""
    try:
        g = get_graph_client()
        nodes_res = g.query("MATCH (n) RETURN id(n) AS id, labels(n)[0] AS label, properties(n) AS props").result_set
        edges_res = g.query("MATCH (n)-[r]->(m) RETURN id(n) AS from_id, id(m) AS to_id, type(r) AS type, properties(r) AS props").result_set

        nodes = []
        for r in nodes_res:
            nid, label, props = r[0], r[1], r[2]
            name = props.get("id") or props.get("device_id") or props.get("ip") or props.get("card_hash") or f"Node_{nid}"
            status = props.get("status", "ACTIVE")

            # Color coding
            if label == "Account":
                color = "#ef4444" if status == "FROZEN" else "#8b5cf6"
                title = f"Account: {name}<br>Status: {status}<br>Risk Score: {props.get('risk_score', 0)}"
                size = 24 if status == "FROZEN" else 20
            elif label == "DeviceFingerprint":
                color = "#dc2626" if status == "BLACKLISTED" else "#f97316"
                title = f"Device: {name}<br>Status: {status}<br>Emulator: {props.get('is_emulator', False)}<br>OS: {props.get('os', 'Unknown')}"
                size = 18
            elif label == "IPAddress":
                color = "#06b6d4"
                title = f"IP: {name}<br>VPN/Proxy: {props.get('is_vpn', False)}<br>ISP: {props.get('isp', 'Unknown')}"
                size = 16
            elif label == "PaymentCard":
                color = "#f43f5e" if status == "REVOKED" else "#eab308"
                title = f"Card: {name}<br>Status: {status}"
                size = 18
            else:
                color = "#94a3b8"
                title = f"{label}: {name}"
                size = 16

            nodes.append({
                "id": nid,
                "label": f"{name}",
                "color": color,
                "title": title,
                "shape": "dot",
                "size": size
            })

        edges = []
        for r in edges_res:
            src, dst, etype, props = r[0], r[1], r[2], r[3]
            edge_color = "#38bdf8" if etype == "TRANSFERRED" else "#a855f7" if etype == "USED_DEVICE" else "#06b6d4" if etype == "USED_IP" else "#f59e0b"
            label_text = f"${props.get('amount'):,.0f}" if etype == "TRANSFERRED" and "amount" in props else etype
            edges.append({
                "from": src,
                "to": dst,
                "label": label_text,
                "color": {"color": edge_color, "highlight": "#ffffff"},
                "arrows": "to",
                "font": {"size": 10, "color": "#94a3b8"}
            })

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
          <style type="text/css">
            #mynetwork {{
              width: 100%;
              height: 560px;
              background-color: #0b0f19;
              border: 1px solid #1e293b;
              border-radius: 8px;
            }}
          </style>
        </head>
        <body>
        <div id="mynetwork"></div>
        <script type="text/javascript">
          var nodes = new vis.DataSet({json.dumps(nodes)});
          var edges = new vis.DataSet({json.dumps(edges)});
          var container = document.getElementById('mynetwork');
          var data = {{ nodes: nodes, edges: edges }};
          var options = {{
            physics: {{
              solver: 'forceAtlas2Based',
              forceAtlas2Based: {{ gravitationalConstant: -60, centralGravity: 0.015, springLength: 110, springConstant: 0.06 }},
              stabilization: {{ iterations: 120 }}
            }},
            nodes: {{
              font: {{ color: '#f8fafc', size: 11, face: 'monospace' }},
              borderWidth: 2,
              shadow: true
            }},
            edges: {{
              smooth: {{ type: 'continuous' }}
            }}
          }};
          var network = new vis.Network(container, data, options);
        </script>
        </body>
        </html>
        """
        components.html(html, height=580)
    except Exception as e:
        st.error(f"Graph rendering error: {e}")


# ------------------------------------------------------------------------------
# Sidebar Controls & 10 Scenario Selector
# ------------------------------------------------------------------------------
with st.sidebar:
    st.image("https://raw.githubusercontent.com/FalkorDB/FalkorDB/main/docs/images/falkordb-logo-color.svg", width=180)
    st.markdown("### 🛡️ SybilShield Command Center")
    st.caption("Track 01: Agents That Act on Connected Data")

    st.markdown("---")
    st.markdown("#### 📂 10 Investigation Scenarios")

    scenario_options = {
        k: f"[{v.get('severity', 'ALERT')}] {v.get('name', f'Scenario {k}')}" for k, v in SCENARIOS.items()
    }
    selected_sc_key = st.selectbox(
        "Choose Pre-Packaged Incident:",
        options=list(scenario_options.keys()),
        format_func=lambda x: scenario_options[x]
    )

    current_sc = SCENARIOS.get(selected_sc_key, {})
    st.markdown(f"**Target:** `{current_sc.get('target_account', 'N/A')}`")
    st.caption(current_sc.get("description", ""))

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚀 Run Scenario", type="primary", use_container_width=True):
            st.session_state["pending_scenario"] = current_sc
            st.session_state["trigger_scenario_run"] = True
    with col_btn2:
        if st.button("📋 Paste Prompt", use_container_width=True):
            st.session_state["prefill_prompt"] = current_sc.get("claude_prompt", "")
            st.rerun()

    # Copy Prompt for Claude / AI Assistants Box
    with st.expander("💬 Natural Language Prompt for Claude / Cursor", expanded=False):
        st.markdown("**Copy & paste into Claude Desktop, Cursor, or Prompt Bar:**")
        st.code(current_sc.get("claude_prompt", ""), language="text")

    st.markdown("---")
    st.markdown("#### 🔍 Manual Target Investigation")
    custom_acc = st.text_input("Account ID", value="MULE_A")
    if st.button("Investigate Custom Account", use_container_width=True):
        st.session_state["pending_manual_acc"] = custom_acc
        st.session_state["trigger_manual_run"] = True

    st.markdown("---")
    st.markdown("#### 🛠️ Database Operations")
    conn_badge = "🌐 FalkorDB Cloud (AWS)" if settings.falkordb_url or settings.falkordb_password else "💻 Local Docker (:6379)"
    st.caption(f"**Active Engine:** `{conn_badge}`")

    if st.button("🔄 Re-Seed Synthetic Graph", use_container_width=True):
        seed_synthetic_fraud_network()
        st.success("Re-seeded all 10 scenario clusters in FalkorDB!")
        time.sleep(1)
        st.rerun()

    if not settings.falkordb_url:
        st.link_button("🌐 Open FalkorDB Browser", "http://localhost:3000", use_container_width=True)

# ------------------------------------------------------------------------------
# Top Metrics Bar
# ------------------------------------------------------------------------------
stats = get_graph_stats()

st.title("🛡️ SybilShield: Autonomous Fraud & Mule Network Disruption")
st.markdown("*Autonomous Graph Reasoning Layer Powered by **FalkorDB GraphBLAS** & **Model Context Protocol (MCP)***")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    status_label = "ONLINE" if stats["online"] else "OFFLINE"
    st.metric("FalkorDB Engine", status_label, f"{stats['latency_ms']:.2f} ms")
with col2:
    st.metric("Hackathon Rule 3", "Load-Bearing", "100% Graph Bound")
with col3:
    st.metric("Total Graph Nodes", stats["nodes"])
with col4:
    st.metric("Total Graph Edges", stats["edges"])
with col5:
    st.metric("Frozen Mule Accounts", stats["frozen"], delta=f"{stats['frozen']} Contained" if stats['frozen'] > 0 else "0")

st.markdown("---")

# ------------------------------------------------------------------------------
# Universal Natural Language Investigation Prompt Console
# ------------------------------------------------------------------------------
st.markdown("### 💬 Autonomous Natural Language Investigation Console")
st.caption(
    "Type **any** arbitrary incident alert, stolen card report, or ad-hoc query and press **Enter** or click **'⚡ Investigate Prompt'**. "
    "SybilShield dynamically resolves entities against FalkorDB, expands the multi-hop graph, and executes containment."
)

default_prompt_val = st.session_state.pop("prefill_prompt", "")
prompt_col, btn_col = st.columns([5, 1])
with prompt_col:
    user_prompt = st.text_input(
        "Enter any natural language query or incident prompt:",
        value=default_prompt_val,
        placeholder="e.g. Account MULE_A just sent $15,000, check if part of a circular ring and freeze if malicious...",
        key="nl_query_input",
        label_visibility="collapsed"
    )
with btn_col:
    run_prompt_clicked = st.button("⚡ Investigate Prompt", type="primary", use_container_width=True)

st.markdown(
    "💡 **Try Arbitrary Prompts:** "
    "`'Account MULE_A sent $15k, investigate circular loop and freeze'` &nbsp;|&nbsp; "
    "`'Issuer alert: card CARD_VISA_STOLEN_9901 stolen, check MULE_E and isolate'` &nbsp;|&nbsp; "
    "`'Audit customer ACC_ALICE'` &nbsp;|&nbsp; "
    "`'BOT_01 suspected emulator bot farm'`"
)

st.markdown("---")

# ------------------------------------------------------------------------------
# Unified Investigation Execution Engine
# ------------------------------------------------------------------------------
should_execute = False
exec_mode = "prompt"
exec_arg = ""

if run_prompt_clicked and user_prompt.strip():
    should_execute = True
    exec_mode = "prompt"
    exec_arg = user_prompt.strip()
elif user_prompt.strip() and user_prompt.strip() != st.session_state.get("last_executed_prompt", ""):
    # Triggered automatically when user hits Enter in text input
    should_execute = True
    exec_mode = "prompt"
    exec_arg = user_prompt.strip()
elif st.session_state.get("trigger_scenario_run", False):
    should_execute = True
    st.session_state["trigger_scenario_run"] = False
    sc = st.session_state.get("pending_scenario", {})
    exec_mode = "direct"
    exec_target = sc.get("target_account", "MULE_A")
    exec_trigger = sc.get("trigger_reason", "Scenario Execution")
elif st.session_state.get("trigger_manual_run", False):
    should_execute = True
    st.session_state["trigger_manual_run"] = False
    exec_mode = "direct"
    exec_target = st.session_state.get("pending_manual_acc", "MULE_A")
    exec_trigger = "Manual Operator Investigation"

if should_execute:
    with st.spinner("Autonomous Agent reasoning across FalkorDB GraphBLAS topology..."):
        agent = SybilShieldAgent()
        if exec_mode == "prompt":
            st.session_state["last_executed_prompt"] = exec_arg
            res = agent.investigate_prompt(exec_arg)
        else:
            res = agent.investigate(exec_target, trigger_reason=exec_trigger)
        st.session_state["last_investigation_result"] = res

# ------------------------------------------------------------------------------
# Main Dashboard Tabs
# ------------------------------------------------------------------------------
tab_inv, tab_canvas, tab_cypher = st.tabs(["🚀 Autonomous Investigation & SAR", "🕸️ Interactive Topology Canvas", "⚡ FalkorDB Cypher Studio"])

# TAB 1: Autonomous Investigation
with tab_inv:
    result = st.session_state.get("last_investigation_result")
    if result:
        if not result.get("success"):
            st.error(result.get("error"))
        else:
            target = result.get("target_account", "UNKNOWN")
            is_fraud = result.get("is_sybil_ring", False)
            conf = result.get("confidence_score", 0.0)
            cluster = result.get("cluster_members", [])

            # NLP Entity Resolution Info Card (if prompt mode was used)
            if "nlp_parsed" in result:
                nlp = result["nlp_parsed"]
                cards_str = ", ".join(nlp.get("detected_cards", [])) or "None"
                devs_str = ", ".join(nlp.get("detected_devices", [])) or "None"
                intent_str = "Containment Requested (Freeze / Blacklist)" if nlp.get("wants_freeze") else "Auditing / Verification"
                
                st.markdown(f"""
                <div class="nlp-pill">
                    <b>🧠 NLP Grounding from FalkorDB:</b><br>
                    • <b>Input Query:</b> <em>"{nlp.get('original_prompt')}"</em><br>
                    • 🎯 <b>Resolved Primary Target:</b> <code>{nlp.get('primary_target')}</code> &nbsp;|&nbsp;
                    💳 <b>Cards Found:</b> <code>{cards_str}</code> &nbsp;|&nbsp;
                    📱 <b>Devices Found:</b> <code>{devs_str}</code> &nbsp;|&nbsp;
                    🛑 <b>Action Intent:</b> <b>{intent_str}</b>
                </div>
                """, unsafe_allow_html=True)

            # Alert Verdict Banner
            if is_fraud:
                st.error(f"### 🚨 [CRITICAL ALERT] CONFIRMED SYBIL NETWORK DISRUPTED | Target: `{target}` | Confidence: {int(conf * 100)}%")
            else:
                st.success(f"### ✅ [VERIFIED] BENIGN TRANSACTION TOPOLOGY | Target: `{target}` | Risk Confidence: {int(conf * 100)}%")

            # 5-Phase Agent Reasoning Trail
            st.markdown("#### 🧠 5-Phase Multi-Hop Agent Reasoning Trail")
            for step in result.get("steps", []):
                phase_name = step.get("phase", "STEP")
                action_desc = step.get("action", "")
                ev = step.get("evidence", {})

                with st.expander(f"📍 **{phase_name}**: {action_desc}", expanded=True):
                    st.json(ev)

            # Executive Forensic SAR Report Box
            st.markdown("#### 📋 Regulatory Suspicious Activity Report (SAR)")
            st.code(result.get("sar_report", ""), language="text")

            st.download_button(
                label="📥 Download SAR Compliance Report (.txt)",
                data=result.get("sar_report", ""),
                file_name=f"SAR_REPORT_{target}.txt",
                mime="text/plain"
            )
    else:
        st.info(
            "👈 Select any of the **10 Scenarios** from the sidebar, or **type any custom incident prompt into the search bar above and press Enter** "
            "to watch SybilShield dynamically inspect, reason, and disrupt fraud rings in real time."
        )

# TAB 2: Live Graph Canvas
with tab_canvas:
    st.subheader("🕸️ Live FalkorDB Force-Directed Topology")
    st.markdown("""
    **Canvas Color Legend:**  
    🔴 **Red Dot:** Frozen Account | 🟣 **Purple Dot:** Active Account | 🟠 **Orange Dot:** Hardware Fingerprint | 🟡 **Yellow Dot:** Payment Card | 🔵 **Cyan Dot:** IP Address | 🔷 **Blue Arrows:** Fund Transfers
    """)
    render_graph_canvas()

# TAB 3: Cypher Query Studio
with tab_cypher:
    st.subheader("⚡ Live Cypher Query Console")
    sample_queries = {
        "1. Detect All Circular Laundering Loops": "MATCH path = (a:Account)-[:TRANSFERRED*2..5]->(a) RETURN [n IN nodes(path) | n.id] AS cycle, length(path) AS hops",
        "2. Run FalkorDB PageRank Centrality": "CALL algo.pageRank('Account', 'TRANSFERRED') YIELD node, score RETURN node.id AS id, score ORDER BY score DESC LIMIT 10",
        "3. Find Accounts Sharing Payment Cards": "MATCH (a1:Account)-[:SHARES_CARD]->(c:PaymentCard)<-[:SHARES_CARD]-(a2:Account) WHERE a1 <> a2 RETURN a1.id, a2.id, c.card_hash",
        "4. Inspect All Frozen Accounts & Audit Nodes": "MATCH (a:Account {status: 'FROZEN'})-[:MITIGATED_BY]->(audit:AgentAudit) RETURN a.id, a.risk_score, audit.reason, audit.timestamp",
        "5. Inspect Blacklisted Hardware & Emulators": "MATCH (d:DeviceFingerprint) WHERE d.is_emulator = true RETURN d.device_id, d.status, d.os"
    }
    
    preset = st.selectbox("Select Preset Query", list(sample_queries.keys()))
    cypher_input = st.text_area("Cypher Query", value=sample_queries[preset], height=90)
    
    if st.button("Execute Cypher on FalkorDB"):
        try:
            g = get_graph_client()
            t0 = time.time()
            res = g.query(cypher_input)
            latency = (time.time() - t0) * 1000
            st.success(f"Execution completed in **{latency:.2f} ms**")
            
            if res.result_set:
                import pandas as pd
                df = pd.DataFrame(res.result_set)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Query executed successfully. Result set is empty.")
        except Exception as e:
            st.error(f"Cypher Error: {e}")
