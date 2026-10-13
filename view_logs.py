import json
import os

def show_audit_logs():
    log_filename = "audit_log.json"
    if not os.path.exists(log_filename):
        print("No audit logs found yet.")
        return
        
    with open(log_filename, "r") as f:
        logs = json.load(f)
        
    print(f"\nTOTAL ORDERS AUDITED: {len(logs)}\n" + "="*50)
    
    for idx, report in enumerate(logs, 1):
        print(f"{idx}. Order ID: {report['order_id']} | Status: {report['status']}")
        print(f"   Timestamp: {report['timestamp']}")
        print(f"   Badge: {report['badge']}")
        if report["audit_flags"]:
            print("   Flags:")
            for flag in report["audit_flags"]:
                print(f"     - {flag}")
        print("-" * 50)

if __name__ == "__main__":
    show_audit_logs()
