import requests
import json

# The local URL where your Flask app is running
WEBHOOK_URL = "http://127.0.0.1:5000/webhook/orders/create"

# Mock Shopify order payload with the correct variant ID
test_order_payload = {
    "id": 101,
    "order_number": 101,
    "line_items": [
        {
            "title": "The Collection Snowboard: Liquid",
            "variant_id": 67715302228211,  # <--- Updated with the real Variant ID
            "quantity": 1                 # Ordering 1 (stock is 0, so this will trigger an oversale!)
        }
    ]
}

headers = {
    "Content-Type": "application/json"
}

print("Sending test webhook payload to Flask server...")
response = requests.post(WEBHOOK_URL, data=json.dumps(test_order_payload), headers=headers)

print(f"Response Status Code: {response.status_code}")
print(f"Response Body: {response.text}")