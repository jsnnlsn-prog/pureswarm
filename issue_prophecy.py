import hmac
import hashlib
import os
from pathlib import Path
from dotenv import load_dotenv

def issue():
    load_dotenv()
    key = os.getenv("PURES_SOVEREIGN_PASSPHRASE", "SOVEREIGN_KEY_FALLBACK")
    content = "RESEARCH: Security trends 2026. EXTERNAL: Shinobi no San initiate Project Deep Guard."
    signature = hmac.new(key.encode(), content.encode(), hashlib.sha256).hexdigest()[:16]

    prophecy_file = Path("data/.prophecy")
    prophecy_file.parent.mkdir(parents=True, exist_ok=True)
    prophecy_file.write_text(f"{signature}:{content}", encoding="utf-8")
    print(f"Prophecy issued to .prophecy: {content}")
    print(f"Signature: {signature}")

if __name__ == "__main__":
    issue()
