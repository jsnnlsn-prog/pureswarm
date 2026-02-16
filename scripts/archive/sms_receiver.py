#!/usr/bin/env python3
"""SMS Receiver - Webhook endpoint for SMS Forwarder app.

Run this on your PC to receive SMS from your phone:
    python sms_receiver.py

Then configure SMS Forwarder app on your Android to POST to:
    http://<your-tailscale-ip>:5555/sms

The receiver writes each SMS to data/sms_inbox/ as JSON for RealSIMProvider.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)

# SMS inbox directory
SMS_INBOX = Path(os.getenv("SMS_INBOX_PATH", "data/sms_inbox"))
SMS_INBOX.mkdir(parents=True, exist_ok=True)

@app.route('/sms', methods=['POST'])
def receive_sms():
    """Receive SMS from forwarder app and save to inbox."""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.json
        else:
            data = request.form.to_dict()

        # Extract SMS fields (SMS Forwarder uses these field names)
        sms_data = {
            "from": data.get("from", data.get("sender", data.get("phone", "unknown"))),
            "body": data.get("body", data.get("text", data.get("message", ""))),
            "timestamp": datetime.now().isoformat(),
            "raw": data  # Keep raw data for debugging
        }

        # Generate unique filename
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(sms_data['body']) % 10000:04d}.json"
        sms_file = SMS_INBOX / filename

        # Write to inbox
        with open(sms_file, 'w') as f:
            json.dump(sms_data, f, indent=2)

        print(f"[SMS] From: {sms_data['from']}")
        print(f"[SMS] Body: {sms_data['body'][:100]}...")
        print(f"[SMS] Saved: {sms_file}")

        return jsonify({"status": "ok", "file": str(sms_file)}), 200

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "inbox": str(SMS_INBOX),
        "files": len(list(SMS_INBOX.glob("*.json")))
    })

@app.route('/', methods=['GET'])
def index():
    """Landing page with setup instructions."""
    return """
    <h1>PureSwarm SMS Receiver</h1>
    <p>POST SMS to <code>/sms</code> with JSON body:</p>
    <pre>{"from": "+1234567890", "body": "Your code is 123456"}</pre>
    <p>Or use SMS Forwarder app fields: sender, text, phone, message</p>
    <p><a href="/health">Health Check</a></p>
    """

if __name__ == "__main__":
    print("=" * 50)
    print("  PureSwarm SMS Receiver")
    print("=" * 50)
    print(f"  Inbox: {SMS_INBOX.absolute()}")
    print(f"  Endpoint: http://0.0.0.0:5555/sms")
    print("=" * 50)
    print()
    print("Configure SMS Forwarder app to POST to this endpoint.")
    print("Press Ctrl+C to stop.")
    print()

    app.run(host='0.0.0.0', port=5555, debug=False)
