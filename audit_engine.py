import json
from datetime import datetime
import os

class FulfillmentGuard:
    def __init__(self):
        self.severity_levels = {
            "VERIFIED": "Verified - Ready for Packing",
            "WARNING": "Warning - Potential Stock Conflict",
            "CRITICAL": "Critical Discrepancy - Do Not Ship"
        }

    def evaluate_order(self, order_data, inventory_db):
        order_id = order_data.get("id")
        line_items = order_data.get("line_items", [])
        
        flags = []
        status = "VERIFIED"

        for item in line_items:
            sku = item.get("sku")
            requested_qty = item.get("quantity")
            title = item.get("title")

            if not sku:
                flags.append(f"CRITICAL: Item '{title}' is missing a valid SKU setting.")
                status = "CRITICAL"
                continue

            inv_record = inventory_db.get(sku)

            if not inv_record:
                flags.append(f"CRITICAL: SKU '{sku}' not found in active location inventory database.")
                status = "CRITICAL"
                continue

            available_stock = inv_record.get("available", 0)
            continue_selling = inv_record.get("continue_selling_out_of_stock", False)

            if requested_qty > available_stock:
                if continue_selling:
                    flags.append(f"WARNING: SKU '{sku}' oversold ({requested_qty} requested vs {available_stock} available). Policy allows out-of-stock sales.")
                    if status != "CRITICAL":
                        status = "WARNING"
                else:
                    flags.append(f"CRITICAL: Insufficient physical inventory for SKU '{sku}' ({requested_qty} requested vs {available_stock} available).")
                    status = "CRITICAL"

            if inv_record.get("recent_app_overwrite"):
                flags.append(f"WARNING: SKU '{sku}' experienced a multi-app inventory sync overwrite in the last 60 minutes.")
                if status != "CRITICAL":
                    status = "WARNING"

        audit_report = {
            "order_id": order_id,
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "badge": self.severity_levels[status],
            "audit_flags": flags
        }

        self.save_to_log(audit_report)
        return audit_report

    def save_to_log(self, report):
        log_filename = "audit_log.json"
        logs = []
        if os.path.exists(log_filename):
            try:
                with open(log_filename, "r") as f:
                    logs = json.load(f)
            except:
                logs = []
        
        logs.append(report)
        with open(log_filename, "w") as f:
            json.dump(logs, f, indent=2)

if __name__ == "__main__":
    mock_inventory = {
        "TSHIRT-BLK-M": {"available": 15, "continue_selling_out_of_stock": False, "recent_app_overwrite": False},
        "TSHIRT-RED-L": {"available": 0, "continue_selling_out_of_stock": True, "recent_app_overwrite": False},
        "HOODIE-GRY-XL": {"available": 1, "continue_selling_out_of_stock": False, "recent_app_overwrite": True},
        "MUG-CERAMIC": {"available": 0, "continue_selling_out_of_stock": False, "recent_app_overwrite": False}
    }

    # Simulate 3 Different Incoming Orders
    test_orders = [
        # Order 1: Clean/Verified Order
        {
            "id": "#1043",
            "line_items": [{"title": "Black T-Shirt (M)", "sku": "TSHIRT-BLK-M", "quantity": 2}]
        },
        # Order 2: Oversold with Allow-Out-of-Stock Policy (Warning)
        {
            "id": "#1044",
            "line_items": [{"title": "Red T-Shirt (L)", "sku": "TSHIRT-RED-L", "quantity": 1}]
        },
        # Order 3: Critical Deficit & Overwrite
        {
            "id": "#1045",
            "line_items": [{"title": "Grey Hoodie (XL)", "sku": "HOODIE-GRY-XL", "quantity": 3}]
        }
    ]

    engine = FulfillmentGuard()
    print("🚀 Processing batch order stream...")
    for order in test_orders:
        report = engine.evaluate_order(order, mock_inventory)
        print(f" -> Audited Order {report['order_id']} | Status: {report['status']}")
    print("✅ Batch complete and logged!")
