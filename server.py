from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- CONFIGURATION (Your 3 lines go right here) ---
SHOPIFY_STORE_DOMAIN = "fulfillment-guard-dev.myshopify.com"
CLIENT_ID = "b072ac0d2451a322600f214e9240c9aa"          # Paste your Client ID here
CLIENT_SECRET = os.environ.get("CLIENT_SECRET") # Paste your Client Secret here

def get_shopify_access_token():
    """Generates an Admin API Access Token using Client Credentials."""
    url = f"https://{SHOPIFY_STORE_DOMAIN}/admin/oauth/access_token"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"[ERROR] Failed to fetch access token ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] Exception during token retrieval: {e}")
        return None

@app.route('/webhook/orders/create', methods=['POST'])
def handle_order_create():
    order_data = request.json
    if not order_data:
        return jsonify({"error": "No JSON payload received"}), 400

    order_id = order_data.get('id')
    line_items = order_data.get('line_items', [])
    
    # Fetch access token dynamically
    token = get_shopify_access_token()
    if not token:
        return jsonify({"error": "Authentication failed"}), 401

    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }

    print(f"--> Received Order #{order_data.get('order_number', order_id)}")

    for item in line_items:
        title = item.get('title')
        variant_id = item.get('variant_id')
        ordered_qty = item.get('quantity', 1)

        print(f"    - Checking Live Stock for: {title} (Variant ID: {variant_id})")

        try:
            # 1. Fetch variant details to get inventory_item_id
            variant_url = f"https://{SHOPIFY_STORE_DOMAIN}/admin/api/2026-01/variants/{variant_id}.json"
            variant_res = requests.get(variant_url, headers=headers)
            
            if variant_res.status_code != 200:
                print(f"[ERROR] Failed to fetch variant ({variant_res.status_code}): {variant_res.text}")
                continue
            
            variant_data = variant_res.json()
            inventory_item_id = variant_data['variant']['inventory_item_id']

            # 2. Query inventory levels endpoint using inventory_item_id
            inventory_url = f"https://{SHOPIFY_STORE_DOMAIN}/admin/api/2026-01/inventory_levels.json?inventory_item_ids={inventory_item_id}"
            inv_res = requests.get(inventory_url, headers=headers)
            
            if inv_res.status_code != 200:
                print(f"[ERROR] Failed to fetch inventory ({inv_res.status_code}): {inv_res.text}")
                continue

            inv_data = inv_res.json()
            available_qty = inv_data['inventory_levels'][0]['available']
            print(f"    - Available Inventory: {available_qty} | Ordered Qty: {ordered_qty}")

            # 3. Check for oversale and cancel if needed
            if available_qty < ordered_qty:
                print(f"[OVERSALE DETECTED] Cancelling Order #{order_id}...")
                cancel_url = f"https://{SHOPIFY_STORE_DOMAIN}/admin/api/2026-01/orders/{order_id}/cancel.json"
                cancel_res = requests.post(cancel_url, headers=headers, json={"reason": "inventory"})
                
                if cancel_res.status_code == 200:
                    print(f"[SUCCESS] Order #{order_id} successfully cancelled.")
                else:
                    print(f"[ERROR] Failed to cancel order ({cancel_res.status_code}): {cancel_res.text}")

        except Exception as e:
            print(f"[ERROR] Exception occurred during inventory check: {e}")

    return jsonify({"status": "success", "message": "Live inventory levels verified"}), 200

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)