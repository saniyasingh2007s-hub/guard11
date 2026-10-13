import os
import hmac
import hashlib
import json
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configure PostgreSQL Database
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///local_guard11.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model for Order Audit Logs
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(100), nullable=False)
    order_name = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=False)  # e.g., 'CANCELLED', 'PASSED', 'FAILED'
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "order_name": self.order_name,
            "status": self.status,
            "reason": self.reason,
            "created_at": self.created_at.isoformat()
        }

# Initialize Database Tables
with app.app_context():
    db.create_all()

CLIENT_SECRET = os.environ.get('CLIENT_SECRET', '')

def verify_shopify_webhook(data, hmac_header):
    if not CLIENT_SECRET:
        return False
    digest = hmac.new(
        CLIENT_SECRET.encode('utf-8'),
        data,
        hashlib.sha256
    ).digest()
    computed_hmac = hashlib.sha256(digest).hexdigest()
    # Base64 encoded HMAC for Shopify validation
    import base64
    computed_b64 = base64.b64encode(digest).decode('utf-8')
    return hmac.compare_digest(computed_b64, hmac_header)

@app.route('/')
def home():
    return jsonify({"status": "Guard11 Service Active", "database": "Connected"})

@app.route('/webhooks/orders/create', methods=['POST'])
def order_created_webhook():
    hmac_header = request.headers.get('X-Shopify-Hmac-Sha256')
    data = request.get_data()

    if hmac_header and not verify_shopify_webhook(data, hmac_header):
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    order_id = str(payload.get('id', 'N/A'))
    order_name = payload.get('name', 'N/A')
    line_items = payload.get('line_items', [])

    canceled = False
    audit_reason = "All items in stock."

    # Perform inventory audit
    for item in line_items:
        # Check stock logic
        quantity = item.get('quantity', 0)
        # Note: If inventory check reveals 0 stock on item
        if item.get('fulfillable_quantity', 1) == 0:
            canceled = True
            audit_reason = f"Item {item.get('title')} was out of stock."
            break

    status_str = "CANCELLED" if canceled else "PASSED"

    # Save record to Database
    try:
        log_entry = AuditLog(
            order_id=order_id,
            order_name=order_name,
            status=status_str,
            reason=audit_reason
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database logging error: {e}")

    return jsonify({"status": "processed", "order_id": order_id, "audit_status": status_str}), 200

if __name__ == '__main__':
    app.run(port=10000)