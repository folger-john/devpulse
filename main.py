"""
DevPulse - Free Online Developer Tools Platform
A collection of fast, free developer utilities with SEO-optimized pages.
"""

import hashlib
import json
import base64
import uuid
import re
import time
import urllib.parse
import secrets
import string
import html
from datetime import datetime, timezone

from collections import defaultdict
from fastapi import FastAPI, Request, Query, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import qrcode
import io

app = FastAPI(title="DevPulse", version="1.0.0")

# ─── Rate Limiting & Request Size Protection ─────────────────────────────────
MAX_BODY_SIZE = 500_000  # 500KB max request body
RATE_LIMIT = 120  # requests per minute per IP
RATE_WINDOW = 60  # seconds

_rate_store: dict[str, list[float]] = defaultdict(list)

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Rate limiting for API endpoints
    if request.url.path.startswith("/api/"):
        ip = request.headers.get("x-real-ip", request.client.host)
        now = time.time()
        # Clean old entries
        _rate_store[ip] = [t for t in _rate_store[ip] if now - t < RATE_WINDOW]
        if len(_rate_store[ip]) >= RATE_LIMIT:
            return JSONResponse(
                {"error": "Rate limit exceeded. Max 120 requests/minute. See /api for paid tiers."},
                status_code=429
            )
        _rate_store[ip].append(now)

        # Request size check
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_SIZE:
            return JSONResponse(
                {"error": f"Request body too large. Max {MAX_BODY_SIZE} bytes."},
                status_code=413
            )

    # API key authentication — paid tiers get higher limits
    api_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
    if api_key and request.url.path.startswith("/api/"):
        key_data = _get_api_key(api_key)
        if key_data:
            tier_limits = {"free": 120, "developer": 5000, "business": 50000, "enterprise": 999999}
            tier_limit = tier_limits.get(key_data["tier"], 120)
            # Re-check with tier limit
            if len(_rate_store[ip]) < tier_limit:
                _rate_store[ip] = []  # Reset — they're within tier limit

    response = await call_next(request)
    return response

# ─── API Key System ──────────────────────────────────────────────────────────
import sqlite3

DB_PATH = "/home/ubuntu/devpulse/data/devpulse.db"

def _init_db():
    import os
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        tier TEXT DEFAULT 'free',
        requests_today INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_used TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS api_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_id INTEGER,
        endpoint TEXT,
        ip TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

_init_db()

def _get_api_key(key: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM api_keys WHERE key = ?", (key,)).fetchone()
    conn.close()
    return dict(row) if row else None

@app.post("/api/keys/create")
async def create_api_key(request: Request):
    body = await request.json()
    email = body.get("email", "").strip()
    if not email or "@" not in email:
        return {"success": False, "error": "Valid email required"}
    conn = sqlite3.connect(DB_PATH)
    existing = conn.execute("SELECT key FROM api_keys WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return {"success": True, "key": existing[0], "message": "Key already exists for this email"}
    import secrets as _sec
    key = "dp_" + _sec.token_hex(24)
    conn.execute("INSERT INTO api_keys (key, email, tier) VALUES (?, ?, 'free')", (key, email))
    conn.commit()
    conn.close()
    return {"success": True, "key": key, "tier": "free", "rate_limit": "120 req/min"}

@app.get("/api/keys/usage")
async def api_key_usage(request: Request):
    api_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
    if not api_key:
        return {"success": False, "error": "API key required (x-api-key header or api_key param)"}
    data = _get_api_key(api_key)
    if not data:
        return {"success": False, "error": "Invalid API key"}
    tier_limits = {"free": 120, "developer": 5000, "business": 50000, "enterprise": 999999}
    return {
        "success": True,
        "tier": data["tier"],
        "rate_limit": f"{tier_limits.get(data['tier'], 120)} req/min",
        "created": data["created_at"],
    }

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ─── Tool Registry ───────────────────────────────────────────────────────────
TOOLS = [
    {"slug": "json-formatter", "name": "JSON Formatter & Validator", "icon": "{ }", "desc": "Format, validate, and beautify JSON data instantly.", "category": "Data"},
    {"slug": "base64", "name": "Base64 Encode/Decode", "icon": "B64", "desc": "Encode or decode Base64 strings online.", "category": "Encoding"},
    {"slug": "url-encode", "name": "URL Encode/Decode", "icon": "%20", "desc": "Percent-encode or decode URLs and query strings.", "category": "Encoding"},
    {"slug": "uuid-generator", "name": "UUID Generator", "icon": "ID", "desc": "Generate random UUIDs (v4) in bulk.", "category": "Generators"},
    {"slug": "hash-generator", "name": "Hash Generator", "icon": "#", "desc": "Generate MD5, SHA-1, SHA-256, SHA-512 hashes.", "category": "Crypto"},
    {"slug": "jwt-decoder", "name": "JWT Decoder", "icon": "JWT", "desc": "Decode and inspect JSON Web Tokens.", "category": "Crypto"},
    {"slug": "color-converter", "name": "Color Converter", "icon": "🎨", "desc": "Convert between HEX, RGB, and HSL color formats.", "category": "CSS"},
    {"slug": "regex-tester", "name": "Regex Tester", "icon": ".*", "desc": "Test regular expressions with real-time matching.", "category": "Text"},
    {"slug": "markdown-preview", "name": "Markdown Preview", "icon": "MD", "desc": "Preview Markdown as rendered HTML in real-time.", "category": "Text"},
    {"slug": "lorem-ipsum", "name": "Lorem Ipsum Generator", "icon": "Aa", "desc": "Generate placeholder text for your designs.", "category": "Generators"},
    {"slug": "qr-code", "name": "QR Code Generator", "icon": "QR", "desc": "Create QR codes from any text or URL.", "category": "Generators"},
    {"slug": "password-generator", "name": "Password Generator", "icon": "🔑", "desc": "Generate strong, random passwords.", "category": "Crypto"},
    {"slug": "timestamp", "name": "Unix Timestamp Converter", "icon": "⏱", "desc": "Convert between Unix timestamps and human dates.", "category": "Data"},
    {"slug": "html-encode", "name": "HTML Entity Encode/Decode", "icon": "&lt;", "desc": "Encode or decode HTML entities.", "category": "Encoding"},
    {"slug": "diff-checker", "name": "Text Diff Checker", "icon": "±", "desc": "Compare two texts and see the differences.", "category": "Text"},
    {"slug": "word-counter", "name": "Word & Character Counter", "icon": "Wc", "desc": "Count words, characters, sentences, and paragraphs.", "category": "Text"},
    {"slug": "css-minifier", "name": "CSS Minifier", "icon": "{ }", "desc": "Minify CSS to reduce file size.", "category": "CSS"},
    {"slug": "http-status", "name": "HTTP Status Code Reference", "icon": "200", "desc": "Complete reference for all HTTP status codes.", "category": "Reference"},
    {"slug": "cron-parser", "name": "Cron Expression Parser", "icon": "⏰", "desc": "Parse and explain cron schedule expressions.", "category": "Data"},
    {"slug": "sql-formatter", "name": "SQL Formatter", "icon": "SQL", "desc": "Format and beautify SQL queries.", "category": "Data"},
    {"slug": "json-to-yaml", "name": "JSON to YAML Converter", "icon": "Y", "desc": "Convert JSON to YAML and back.", "category": "Data"},
    {"slug": "slug-generator", "name": "URL Slug Generator", "icon": "/", "desc": "Convert text to URL-friendly slugs.", "category": "Text"},
    {"slug": "chmod-calculator", "name": "Chmod Calculator", "icon": "777", "desc": "Calculate Linux file permissions.", "category": "Reference"},
    {"slug": "ip-lookup", "name": "IP Address Lookup", "icon": "IP", "desc": "Look up your public IP address and details.", "category": "Reference"},
    {"slug": "text-case", "name": "Text Case Converter", "icon": "Aa", "desc": "Convert text to UPPER, lower, Title, camelCase, and more.", "category": "Text"},
]

CATEGORIES = sorted(set(t["category"] for t in TOOLS))

# ─── Pages ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "tools": TOOLS,
        "categories": CATEGORIES,
    })

@app.get("/tool/{slug}", response_class=HTMLResponse)
async def tool_page(request: Request, slug: str):
    tool = next((t for t in TOOLS if t["slug"] == slug), None)
    if not tool:
        return templates.TemplateResponse(request, "404.html", status_code=404)
    return templates.TemplateResponse(request, f"tools/{slug}.html", {
        "tool": tool,
        "tools": TOOLS,
    })

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse(request, "about.html")

@app.get("/api", response_class=HTMLResponse)
async def api_docs(request: Request):
    return templates.TemplateResponse(request, "api_docs.html", {"tools": TOOLS})

@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse(request, "privacy.html")

@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse(request, "terms.html")

@app.get("/health")
async def health():
    return {"status": "ok", "tools": len(TOOLS), "version": "1.1.0"}

@app.get("/google8fb40758dad9eb73.html")
async def google_verify():
    return HTMLResponse("google-site-verification: google8fb40758dad9eb73.html")

@app.get("/d3vpuls3t00ls2026.txt")
async def indexnow_key():
    return HTMLResponse("d3vpuls3t00ls2026", media_type="text/plain")

# ─── API Endpoints ───────────────────────────────────────────────────────────

@app.post("/api/json-format")
async def api_json_format(request: Request):
    body = await request.json()
    text = body.get("text", "")
    indent = body.get("indent", 2)
    try:
        parsed = json.loads(text)
        formatted = json.dumps(parsed, indent=indent, ensure_ascii=False)
        return {"success": True, "result": formatted, "valid": True}
    except json.JSONDecodeError as e:
        return {"success": False, "error": str(e), "valid": False}

@app.post("/api/base64")
async def api_base64(request: Request):
    body = await request.json()
    text = body.get("text", "")
    mode = body.get("mode", "encode")
    try:
        if mode == "encode":
            result = base64.b64encode(text.encode()).decode()
        else:
            result = base64.b64decode(text.encode()).decode()
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/url-encode")
async def api_url_encode(request: Request):
    body = await request.json()
    text = body.get("text", "")
    mode = body.get("mode", "encode")
    if mode == "encode":
        result = urllib.parse.quote(text, safe="")
    else:
        result = urllib.parse.unquote(text)
    return {"success": True, "result": result}

@app.post("/api/uuid")
async def api_uuid(request: Request):
    body = await request.json()
    count = min(body.get("count", 1), 100)
    uuids = [str(uuid.uuid4()) for _ in range(count)]
    return {"success": True, "result": uuids}

@app.post("/api/hash")
async def api_hash(request: Request):
    body = await request.json()
    text = body.get("text", "")
    algorithms = ["md5", "sha1", "sha256", "sha512"]
    results = {}
    for algo in algorithms:
        h = hashlib.new(algo)
        h.update(text.encode())
        results[algo] = h.hexdigest()
    return {"success": True, "result": results}

@app.post("/api/jwt-decode")
async def api_jwt_decode(request: Request):
    body = await request.json()
    token = body.get("token", "")
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {"success": False, "error": "Invalid JWT format (expected 3 parts)"}

        def decode_part(part):
            padding = 4 - len(part) % 4
            if padding != 4:
                part += "=" * padding
            return json.loads(base64.urlsafe_b64decode(part).decode())

        header = decode_part(parts[0])
        payload = decode_part(parts[1])

        exp_info = None
        if "exp" in payload:
            exp_dt = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            is_expired = exp_dt < datetime.now(timezone.utc)
            exp_info = {"expires": exp_dt.isoformat(), "expired": is_expired}

        return {"success": True, "header": header, "payload": payload, "expiry": exp_info}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/color-convert")
async def api_color_convert(request: Request):
    body = await request.json()
    color = body.get("color", "").strip()
    try:
        r, g, b = 0, 0, 0
        if color.startswith("#"):
            hex_color = color.lstrip("#")
            if len(hex_color) == 3:
                hex_color = "".join(c * 2 for c in hex_color)
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        elif color.startswith("rgb"):
            nums = re.findall(r"\d+", color)
            r, g, b = int(nums[0]), int(nums[1]), int(nums[2])
        else:
            nums = color.replace(",", " ").split()
            r, g, b = int(nums[0]), int(nums[1]), int(nums[2])

        hex_val = f"#{r:02x}{g:02x}{b:02x}"
        rgb_val = f"rgb({r}, {g}, {b})"

        r2, g2, b2 = r / 255, g / 255, b / 255
        cmax, cmin = max(r2, g2, b2), min(r2, g2, b2)
        delta = cmax - cmin
        l = (cmax + cmin) / 2
        s = 0 if delta == 0 else delta / (1 - abs(2 * l - 1))
        if delta == 0:
            h = 0
        elif cmax == r2:
            h = 60 * (((g2 - b2) / delta) % 6)
        elif cmax == g2:
            h = 60 * (((b2 - r2) / delta) + 2)
        else:
            h = 60 * (((r2 - g2) / delta) + 4)
        hsl_val = f"hsl({int(h)}, {int(s * 100)}%, {int(l * 100)}%)"

        return {"success": True, "hex": hex_val, "rgb": rgb_val, "hsl": hsl_val, "r": r, "g": g, "b": b}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/password")
async def api_password(request: Request):
    body = await request.json()
    length = min(max(body.get("length", 16), 4), 128)
    use_upper = body.get("uppercase", True)
    use_lower = body.get("lowercase", True)
    use_digits = body.get("digits", True)
    use_symbols = body.get("symbols", True)
    count = min(body.get("count", 1), 20)

    chars = ""
    if use_lower: chars += string.ascii_lowercase
    if use_upper: chars += string.ascii_uppercase
    if use_digits: chars += string.digits
    if use_symbols: chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"
    if not chars: chars = string.ascii_letters + string.digits

    passwords = ["".join(secrets.choice(chars) for _ in range(length)) for _ in range(count)]
    return {"success": True, "result": passwords}

@app.post("/api/timestamp")
async def api_timestamp(request: Request):
    body = await request.json()
    mode = body.get("mode", "now")

    if mode == "now":
        now = datetime.now(timezone.utc)
        return {
            "success": True,
            "unix": int(now.timestamp()),
            "unix_ms": int(now.timestamp() * 1000),
            "iso": now.isoformat(),
            "human": now.strftime("%B %d, %Y %H:%M:%S UTC"),
        }
    elif mode == "to_human":
        ts = body.get("timestamp", 0)
        if ts > 1e12:
            ts = ts / 1000
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return {
            "success": True,
            "iso": dt.isoformat(),
            "human": dt.strftime("%B %d, %Y %H:%M:%S UTC"),
            "unix": int(ts),
        }
    elif mode == "to_unix":
        date_str = body.get("date", "")
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return {
            "success": True,
            "unix": int(dt.timestamp()),
            "unix_ms": int(dt.timestamp() * 1000),
        }

@app.post("/api/html-encode")
async def api_html_encode(request: Request):
    body = await request.json()
    text = body.get("text", "")
    mode = body.get("mode", "encode")
    if mode == "encode":
        result = html.escape(text)
    else:
        result = html.unescape(text)
    return {"success": True, "result": result}

@app.post("/api/word-count")
async def api_word_count(request: Request):
    body = await request.json()
    text = body.get("text", "")
    words = len(text.split()) if text.strip() else 0
    chars = len(text)
    chars_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
    sentences = len(re.split(r'[.!?]+', text.strip())) - 1 if text.strip() else 0
    paragraphs = len([p for p in text.split("\n\n") if p.strip()]) if text.strip() else 0
    lines = text.count("\n") + 1 if text else 0
    read_time = max(1, round(words / 200))

    return {
        "success": True,
        "words": words,
        "characters": chars,
        "characters_no_spaces": chars_no_spaces,
        "sentences": max(sentences, 0),
        "paragraphs": paragraphs,
        "lines": lines,
        "read_time_minutes": read_time,
    }

@app.post("/api/css-minify")
async def api_css_minify(request: Request):
    body = await request.json()
    css = body.get("text", "")
    minified = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    minified = re.sub(r'\s+', ' ', minified)
    minified = re.sub(r'\s*([{}:;,])\s*', r'\1', minified)
    minified = minified.strip()

    original_size = len(css.encode())
    minified_size = len(minified.encode())
    savings = round((1 - minified_size / original_size) * 100, 1) if original_size > 0 else 0

    return {"success": True, "result": minified, "original_size": original_size, "minified_size": minified_size, "savings_percent": savings}

@app.post("/api/lorem-ipsum")
async def api_lorem_ipsum(request: Request):
    body = await request.json()
    paragraphs = min(body.get("paragraphs", 3), 20)

    base = [
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
        "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.",
        "Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.",
        "Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem.",
        "Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur.",
        "Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur.",
        "At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident.",
    ]

    result = []
    for i in range(paragraphs):
        result.append(base[i % len(base)])

    return {"success": True, "result": "\n\n".join(result)}

@app.get("/api/qr-code")
async def api_qr_code(text: str = Query(...), size: int = Query(300)):
    qr = qrcode.QRCode(version=1, box_size=max(1, size // 30), border=4)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

@app.post("/api/cron-parse")
async def api_cron_parse(request: Request):
    body = await request.json()
    expr = body.get("expression", "")
    try:
        from croniter import croniter
        cron = croniter(expr, datetime.now())
        next_runs = []
        for _ in range(5):
            next_runs.append(cron.get_next(datetime).strftime("%Y-%m-%d %H:%M:%S"))

        parts = expr.split()
        field_names = ["minute", "hour", "day (month)", "month", "day (week)"]
        explanation = []
        for i, (part, name) in enumerate(zip(parts[:5], field_names)):
            explanation.append(f"{name}: {part}")

        return {"success": True, "next_runs": next_runs, "fields": explanation}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/sql-format")
async def api_sql_format(request: Request):
    body = await request.json()
    sql = body.get("text", "")
    keywords = [
        "SELECT", "FROM", "WHERE", "AND", "OR", "JOIN", "LEFT JOIN", "RIGHT JOIN",
        "INNER JOIN", "OUTER JOIN", "ON", "GROUP BY", "ORDER BY", "HAVING", "LIMIT",
        "INSERT INTO", "VALUES", "UPDATE", "SET", "DELETE FROM", "CREATE TABLE",
        "ALTER TABLE", "DROP TABLE", "UNION", "UNION ALL", "AS", "IN", "NOT IN",
        "BETWEEN", "LIKE", "IS NULL", "IS NOT NULL", "EXISTS", "CASE", "WHEN",
        "THEN", "ELSE", "END", "DISTINCT", "COUNT", "SUM", "AVG", "MAX", "MIN",
    ]
    formatted = sql.strip()
    for kw in sorted(keywords, key=len, reverse=True):
        pattern = re.compile(r'\b' + kw + r'\b', re.IGNORECASE)
        formatted = pattern.sub(kw, formatted)

    newline_before = ["SELECT", "FROM", "WHERE", "AND", "OR", "JOIN", "LEFT JOIN",
                      "RIGHT JOIN", "INNER JOIN", "GROUP BY", "ORDER BY", "HAVING",
                      "LIMIT", "UNION", "UNION ALL"]
    for kw in newline_before:
        formatted = formatted.replace(f" {kw} ", f"\n{kw} ")
        formatted = formatted.replace(f" {kw}\n", f"\n{kw}\n")

    return {"success": True, "result": formatted}

@app.post("/api/json-to-yaml")
async def api_json_to_yaml(request: Request):
    body = await request.json()
    text = body.get("text", "")
    mode = body.get("mode", "json_to_yaml")
    try:
        if mode == "json_to_yaml":
            data = json.loads(text)
            def to_yaml(obj, indent=0):
                lines = []
                pad = "  " * indent
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if isinstance(v, (dict, list)):
                            lines.append(f"{pad}{k}:")
                            lines.append(to_yaml(v, indent + 1))
                        else:
                            val = "true" if v is True else "false" if v is False else "null" if v is None else f'"{v}"' if isinstance(v, str) else str(v)
                            lines.append(f"{pad}{k}: {val}")
                elif isinstance(obj, list):
                    for item in obj:
                        if isinstance(item, (dict, list)):
                            lines.append(f"{pad}-")
                            lines.append(to_yaml(item, indent + 1))
                        else:
                            val = "true" if item is True else "false" if item is False else "null" if item is None else f'"{item}"' if isinstance(item, str) else str(item)
                            lines.append(f"{pad}- {val}")
                return "\n".join(lines)
            result = to_yaml(data)
        else:
            # Simple YAML to JSON (basic key: value parsing)
            lines = text.strip().split("\n")
            data = {}
            for line in lines:
                if ":" in line:
                    key, val = line.split(":", 1)
                    val = val.strip().strip('"').strip("'")
                    if val.lower() == "true": val = True
                    elif val.lower() == "false": val = False
                    elif val.lower() == "null": val = None
                    else:
                        try: val = int(val)
                        except ValueError:
                            try: val = float(val)
                            except ValueError: pass
                    data[key.strip()] = val
            result = json.dumps(data, indent=2)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/slug-generate")
async def api_slug_generate(request: Request):
    body = await request.json()
    text = body.get("text", "")
    separator = body.get("separator", "-")
    slug = text.lower().strip()
    slug = re.sub(r'[àáâãäå]', 'a', slug)
    slug = re.sub(r'[èéêë]', 'e', slug)
    slug = re.sub(r'[ìíîï]', 'i', slug)
    slug = re.sub(r'[òóôõö]', 'o', slug)
    slug = re.sub(r'[ùúûü]', 'u', slug)
    slug = re.sub(r'[ñ]', 'n', slug)
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', separator, slug)
    slug = slug.strip(separator)
    return {"success": True, "result": slug}

@app.post("/api/text-case")
async def api_text_case(request: Request):
    body = await request.json()
    text = body.get("text", "")
    results = {
        "UPPER CASE": text.upper(),
        "lower case": text.lower(),
        "Title Case": text.title(),
        "Sentence case": text[0].upper() + text[1:].lower() if text else "",
        "camelCase": "".join(w.capitalize() if i > 0 else w.lower() for i, w in enumerate(text.split())),
        "PascalCase": "".join(w.capitalize() for w in text.split()),
        "snake_case": re.sub(r'[\s-]+', '_', text.lower().strip()),
        "kebab-case": re.sub(r'[\s_]+', '-', text.lower().strip()),
        "CONSTANT_CASE": re.sub(r'[\s-]+', '_', text.upper().strip()),
        "dot.case": re.sub(r'[\s-]+', '.', text.lower().strip()),
    }
    return {"success": True, "result": results}

@app.get("/api/ip-lookup")
async def api_ip_lookup(request: Request):
    ip = request.headers.get("x-real-ip", request.headers.get("x-forwarded-for", request.client.host))
    return {"success": True, "ip": ip}

# ─── Sitemap for SEO ─────────────────────────────────────────────────────────

@app.get("/sitemap.xml")
async def sitemap(request: Request):
    base_url = "https://devpulse.tools"
    urls = [f"  <url><loc>{base_url}/</loc><priority>1.0</priority></url>"]
    for tool in TOOLS:
        urls.append(f"  <url><loc>{base_url}/tool/{tool['slug']}</loc><priority>0.8</priority></url>")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""
    return HTMLResponse(content=xml, media_type="application/xml")

@app.get("/robots.txt")
async def robots(request: Request):
    return HTMLResponse(content="User-agent: *\nAllow: /\nSitemap: https://devpulse.tools/sitemap.xml", media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
