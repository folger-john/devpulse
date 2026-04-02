"""
DevPulse Test Suite
Run: python3 tests.py
"""

import sys
import json
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)
passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name} {detail}")

print("=" * 60)
print("DevPulse Test Suite")
print("=" * 60)

# ─── Page Tests ──────────────────────────────────────────────
print("\n--- Page Tests ---")

r = client.get("/")
test("Homepage loads", r.status_code == 200)
test("Homepage has tool links", "json-formatter" in r.text)

r = client.get("/about")
test("About page loads", r.status_code == 200)

r = client.get("/api")
test("API docs page loads", r.status_code == 200)

r = client.get("/sitemap.xml")
test("Sitemap loads", r.status_code == 200)
test("Sitemap has URLs", "<url>" in r.text)

r = client.get("/robots.txt")
test("Robots.txt loads", r.status_code == 200)

r = client.get("/tool/nonexistent")
test("404 for missing tool", r.status_code == 404)

# ─── Tool Page Tests ─────────────────────────────────────────
print("\n--- Tool Page Tests ---")
tools = ['json-formatter', 'base64', 'url-encode', 'uuid-generator', 'hash-generator',
         'jwt-decoder', 'color-converter', 'regex-tester', 'markdown-preview', 'lorem-ipsum',
         'qr-code', 'password-generator', 'timestamp', 'html-encode', 'diff-checker',
         'word-counter', 'css-minifier', 'http-status', 'cron-parser', 'sql-formatter']

for slug in tools:
    r = client.get(f"/tool/{slug}")
    test(f"/tool/{slug}", r.status_code == 200)

# ─── API Tests ───────────────────────────────────────────────
print("\n--- API Tests ---")

# JSON Formatter
r = client.post("/api/json-format", json={"text": '{"name":"test","value":42}', "indent": 2})
data = r.json()
test("JSON format - valid", data["success"] and data["valid"])
test("JSON format - formatted output", '"name": "test"' in data["result"])

r = client.post("/api/json-format", json={"text": "not json"})
data = r.json()
test("JSON format - invalid input", not data["success"] and not data["valid"])

# Base64
r = client.post("/api/base64", json={"text": "Hello World", "mode": "encode"})
data = r.json()
test("Base64 encode", data["result"] == "SGVsbG8gV29ybGQ=")

r = client.post("/api/base64", json={"text": "SGVsbG8gV29ybGQ=", "mode": "decode"})
data = r.json()
test("Base64 decode", data["result"] == "Hello World")

# URL Encode
r = client.post("/api/url-encode", json={"text": "hello world&foo=bar", "mode": "encode"})
data = r.json()
test("URL encode", "hello%20world" in data["result"])

r = client.post("/api/url-encode", json={"text": "hello%20world", "mode": "decode"})
data = r.json()
test("URL decode", data["result"] == "hello world")

# UUID
r = client.post("/api/uuid", json={"count": 5})
data = r.json()
test("UUID generation", len(data["result"]) == 5)
test("UUID format valid", all(len(u) == 36 and u.count("-") == 4 for u in data["result"]))

# Hash
r = client.post("/api/hash", json={"text": "test"})
data = r.json()
test("Hash - MD5", data["result"]["md5"] == "098f6bcd4621d373cade4e832627b4f6")
test("Hash - SHA256", data["result"]["sha256"] == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08")

# JWT Decode
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
r = client.post("/api/jwt-decode", json={"token": token})
data = r.json()
test("JWT decode header", data["header"]["alg"] == "HS256")
test("JWT decode payload", data["payload"]["name"] == "John Doe")

r = client.post("/api/jwt-decode", json={"token": "invalid"})
data = r.json()
test("JWT decode invalid", not data["success"])

# Color Convert
r = client.post("/api/color-convert", json={"color": "#ff5733"})
data = r.json()
test("Color HEX input", data["rgb"] == "rgb(255, 87, 51)")

r = client.post("/api/color-convert", json={"color": "rgb(100, 200, 50)"})
data = r.json()
test("Color RGB input", "#64c832" in data["hex"])

# Password
r = client.post("/api/password", json={"length": 20, "count": 3})
data = r.json()
test("Password count", len(data["result"]) == 3)
test("Password length", all(len(p) == 20 for p in data["result"]))

# Timestamp
r = client.post("/api/timestamp", json={"mode": "now"})
data = r.json()
test("Timestamp now", data["success"] and "unix" in data)

r = client.post("/api/timestamp", json={"mode": "to_human", "timestamp": 1711900800})
data = r.json()
test("Timestamp to human", "2024" in data["human"])

# HTML Encode
r = client.post("/api/html-encode", json={"text": "<div>test</div>", "mode": "encode"})
data = r.json()
test("HTML encode", "&lt;div&gt;" in data["result"])

r = client.post("/api/html-encode", json={"text": "&lt;div&gt;test&lt;/div&gt;", "mode": "decode"})
data = r.json()
test("HTML decode", data["result"] == "<div>test</div>")

# Word Count
r = client.post("/api/word-count", json={"text": "Hello world. This is a test. Three sentences here."})
data = r.json()
test("Word count", data["words"] == 9)
test("Sentence count", data["sentences"] >= 2)

# CSS Minify
r = client.post("/api/css-minify", json={"text": ".container {\n  display: flex;\n  color: red;\n}"})
data = r.json()
test("CSS minify", len(data["result"]) < len(".container {\n  display: flex;\n  color: red;\n}"))
test("CSS savings", data["savings_percent"] > 0)

# Lorem Ipsum
r = client.post("/api/lorem-ipsum", json={"paragraphs": 3})
data = r.json()
test("Lorem ipsum", "Lorem ipsum" in data["result"])

# Cron Parse
r = client.post("/api/cron-parse", json={"expression": "*/5 * * * *"})
data = r.json()
test("Cron parse success", data["success"])
test("Cron next runs", len(data["next_runs"]) == 5)

# SQL Format
r = client.post("/api/sql-format", json={"text": "select * from users where id = 1"})
data = r.json()
test("SQL format", "SELECT" in data["result"])

# QR Code
r = client.get("/api/qr-code?text=https://devpulse.dev&size=200")
test("QR code generation", r.status_code == 200)
test("QR code is PNG", r.headers["content-type"] == "image/png")

# ─── Summary ─────────────────────────────────────────────────
print("\n" + "=" * 60)
total = passed + failed
print(f"Results: {passed}/{total} passed, {failed} failed")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
