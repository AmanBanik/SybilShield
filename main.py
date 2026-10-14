import sys
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.agent.core import SybilShieldAgent
from src.demo_scenarios import SCENARIOS
from src.db.connection import test_db_connection
from src.db.seed import seed_synthetic_fraud_network


def print_banner():
    banner = """
    +=======================================================================+
    |               S Y B I L S H I E L D   A G E N T                       |
    |      Autonomous Fraud & Mule Network Disruption on FalkorDB           |
    +=======================================================================+
    """
    print(banner)


def run_scenario(scenario_key: str):
    scenario = SCENARIOS.get(scenario_key)
    if not scenario:
        print(f"[-] Invalid scenario key: {scenario_key}")
        return

    print(f"\n[*] Launching Scenario: {scenario['name']}")
    print(f"[*] Description: {scenario['description']}")
    print(f"[*] Target Account: {scenario['target_account']}")
    print(f"[*] Trigger Motivation: {scenario['trigger_reason']}\n")

    agent = SybilShieldAgent()
    result = agent.investigate(
        target_account_id=scenario["target_account"],
        trigger_reason=scenario["trigger_reason"]
    )

    if result.get("success"):
        print(result["sar_report"])
    else:
        print(f"[-] Investigation Failed: {result.get('error')}")


def interactive_menu():
    print_banner()
    if not test_db_connection():
        print("[!] ERROR: Cannot connect to FalkorDB on localhost:6379.")
        print("[!] Please run: docker compose up -d\n")
        sys.exit(1)

    while True:
        print("\nAvailable Commands:")
        print("  1. Run Scenario 1: Ghost Emulator Circular Ring (MULE_A)")
        print("  2. Run Scenario 2: Stolen Card Structuring Funnel (MULE_E)")
        print("  3. Run Scenario 3: Benign Customer Audit (ACC_ALICE)")
        print("  4. Freeform Natural Language Incident Prompt (Type any alert/query)")
        print("  5. Custom Account ID Investigation")
        print("  6. Reset & Re-Seed Synthetic Fraud Graph")
        print("  7. Launch FastMCP Server (stdio mode)")
        print("  8. Launch Streamlit Web Dashboard (http://localhost:8501)")
        print("  0. Exit")

        choice = input("\nSelect an option [0-8]: ").strip()

        if choice in ["1", "2", "3"]:
            run_scenario(choice)
        elif choice == "4":
            prompt = input("Enter incident alert or prompt: ").strip()
            if prompt:
                agent = SybilShieldAgent()
                res = agent.investigate_prompt(prompt)
                print(res.get("sar_report", res.get("error")))
        elif choice == "5":
            acc_id = input("Enter Account ID to investigate (e.g. MULE_A, MULE_B): ").strip()
            if acc_id:
                agent = SybilShieldAgent()
                res = agent.investigate(acc_id, trigger_reason="Manual Operator Investigation")
                print(res.get("sar_report", res.get("error")))
        elif choice == "6":
            seed_synthetic_fraud_network()
        elif choice == "7":
            print("[*] Launching FastMCP Server on stdio. Press Ctrl+C to stop.")
            from src.mcp.server import mcp
            mcp.run()
        elif choice == "8":
            import subprocess
            print("[*] Launching Streamlit Dashboard at http://localhost:8501...")
            subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
        elif choice == "0":
            print("[*] Exiting SybilShield.")
            break
        else:
            print("[-] Invalid choice. Please select 0-8.")


def main():
    parser = argparse.ArgumentParser(description="SybilShield Agent CLI")
    parser.add_argument("--scenario", "-s", choices=[str(i) for i in range(1, 11)], help="Run a specific scenario (1-10)")
    parser.add_argument("--prompt", "-p", type=str, help="Investigate using a freeform natural language query")
    parser.add_argument("--account", "-a", type=str, help="Investigate a specific account ID")
    parser.add_argument("--seed", action="store_true", help="Re-seed the synthetic graph in FalkorDB")
    parser.add_argument("--url", type=str, help="Custom FalkorDB connection URL (e.g. falkor://falkordb:pass@host:port)")
    parser.add_argument("--mcp", action="store_true", help="Run the FastMCP server directly")
    parser.add_argument("--sse", action="store_true", help="Launch FastMCP in SSE mode for cloud clients")
    parser.add_argument("--port", type=int, default=8000, help="Port for FastMCP SSE server (default: 8000)")
    parser.add_argument("--ui", action="store_true", help="Launch the Streamlit Web Dashboard")

    args = parser.parse_args()

    if args.url:
        from src.config import settings
        settings.falkordb_url = args.url

    if args.seed:
        seed_synthetic_fraud_network(url=args.url)
    elif args.mcp or args.sse:
        from src.mcp.server import mcp
        if args.sse:
            print(f"[*] Starting FastMCP with SSE transport on port {args.port}...")
            mcp.run(transport="sse", host="0.0.0.0", port=args.port)
        else:
            mcp.run(transport="stdio")
    elif args.ui:
        import subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    elif args.scenario:
        print_banner()
        run_scenario(args.scenario)
    elif args.prompt:
        print_banner()
        agent = SybilShieldAgent()
        res = agent.investigate_prompt(args.prompt)
        print(res.get("sar_report", res.get("error")))
    elif args.account:
        print_banner()
        agent = SybilShieldAgent()
        res = agent.investigate(args.account, trigger_reason="CLI Invocation")
        print(res.get("sar_report", res.get("error")))
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
