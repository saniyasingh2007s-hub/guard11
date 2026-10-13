import json
import os

def generate_dashboard():
    log_filename = "audit_log.json"
    if not os.path.exists(log_filename):
        print("No audit logs found yet.")
        return

    with open(log_filename, "r", encoding="utf-8") as f:
        logs = json.load(f)

    total = len(logs)
    critical = sum(1 for l in logs if l["status"] == "CRITICAL")
    warning = sum(1 for l in logs if l["status"] == "WARNING")
    verified = sum(1 for l in logs if l["status"] == "VERIFIED")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Fulfillment Guard Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #1e293b; margin: 0; padding: 40px; }}
        .container {{ max-width: 900px; margin: auto; }}
        h1 {{ margin-bottom: 5px; color: #0f172a; }}
        .subtitle {{ color: #64748b; margin-bottom: 30px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }}
        .card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
        .card h3 {{ margin: 0 0 10px 0; font-size: 14px; color: #64748b; text-transform: uppercase; }}
        .card .value {{ font-size: 28px; font-weight: bold; }}
        .order-card {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 6px solid #cbd5e1; }}
        .order-card.CRITICAL {{ border-left-color: #ef4444; background: #fef2f2; }}
        .order-card.WARNING {{ border-left-color: #f59e0b; background: #fffbeb; }}
        .order-card.VERIFIED {{ border-left-color: #22c55e; background: #f0fdf4; }}
        .order-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-weight: bold; font-size: 18px; }}
        .badge {{ padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; color: white; }}
        .badge.CRITICAL {{ background: #ef4444; }}
        .badge.WARNING {{ background: #f59e0b; }}
        .badge.VERIFIED {{ background: #22c55e; }}
        .timestamp {{ font-size: 13px; color: #64748b; margin-bottom: 10px; }}
        ul {{ margin: 5px 0 0 20px; padding: 0; }}
        li {{ color: #334155; font-size: 14px; margin-bottom: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Fulfillment Guard</h1>
        <div class="subtitle">Pre-fulfillment inventory discrepancy & error detection dashboard</div>
        
        <div class="metrics">
            <div class="card"><h3>Total Audited</h3><div class="value">{total}</div></div>
            <div class="card"><h3>Verified</h3><div class="value" style="color: #22c55e;">{verified}</div></div>
            <div class="card"><h3>Warnings</h3><div class="value" style="color: #f59e0b;">{warning}</div></div>
            <div class="card"><h3>Critical Blocked</h3><div class="value" style="color: #ef4444;">{critical}</div></div>
        </div>

        <h2>📦 Order Audit Stream</h2>
"""

    for report in reversed(logs):
        status = report["status"]
        order_id = report["order_id"]
        timestamp = report["timestamp"]
        badge = report["badge"]
        flags = report["audit_flags"]

        flags_html = ""
        if flags:
            flags_html = "<b>Audit Flags:</b><ul>" + "".join([f"<li>{flag}</li>" for flag in flags]) + "</ul>"
        else:
            flags_html = "<i>No discrepancies detected. Order cleared for packing.</i>"

        html_content += f"""
        <div class="order-card {status}">
            <div class="order-header">
                <span>Order {order_id}</span>
                <span class="badge {status}">{status}</span>
            </div>
            <div class="timestamp">Timestamp: {timestamp} &nbsp;|&nbsp; {badge}</div>
            {flags_html}
        </div>
        """

    html_content += """
    </div>
</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ Dashboard generated successfully as 'index.html'!")

if __name__ == "__main__":
    generate_dashboard()
