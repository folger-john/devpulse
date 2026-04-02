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

from fastapi import FastAPI, Request, Query, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import qrcode
import io

app = FastAPI(title="DevPulse", version="1.0.0")
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
        return HTMLResponse("Tool not found", status_code=404)
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

# ─── Sitemap for SEO ─────────────────────────────────────────────────────────

@app.get("/sitemap.xml")
async def sitemap(request: Request):
    base_url = str(request.base_url).rstrip("/")
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
    base_url = str(request.base_url).rstrip("/")
    return HTMLResponse(content=f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml", media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
