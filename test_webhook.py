"""
Local test runner — validates the full pipeline without a phone.
Usage:
  python test_webhook.py <image_path>   # test a real screenshot
  python test_webhook.py                # generates a dummy PNG
"""
import sys
import base64
import json
import struct
import zlib
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

load_dotenv()

SERVER = "http://localhost:5000"
SECRET = os.environ.get("WEBHOOK_SECRET", "")


def tiny_png() -> bytes:
    """Returns a 1x1 white PNG — enough to test the pipeline shape."""
    def mk_chunk(name: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(name + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", crc)

    ihdr = mk_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw = b"\x00\xff\xff\xff"
    idat = mk_chunk(b"IDAT", zlib.compress(raw))
    iend = mk_chunk(b"IEND", b"")
    return b"\x89PNG\r\n\x1a\n" + ihdr + idat + iend


def run_test(image_bytes: bytes, label: str):
    image_b64 = base64.b64encode(image_bytes).decode()
    payload = {
        "image_data": image_b64,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    headers = {"Content-Type": "application/json"}
    if SECRET:
        headers["X-Secret"] = SECRET

    print(f"\n[{label}] POST {SERVER}/webhook ...")
    r = requests.post(f"{SERVER}/webhook", json=payload, headers=headers, timeout=30)
    print(f"  Status : {r.status_code}")
    print(f"  Response: {json.dumps(r.json(), indent=2)}")


def test_health():
    r = requests.get(f"{SERVER}/health", timeout=5)
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    print(f"[health] OK — {r.json()}")


if __name__ == "__main__":
    test_health()

    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, "rb") as f:
            image_bytes = f.read()
        run_test(image_bytes, path)
    else:
        print("No image path given — sending 1x1 dummy PNG (tests transport, not classification)")
        run_test(tiny_png(), "dummy-png")
