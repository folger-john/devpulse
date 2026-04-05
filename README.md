<div align="center">

# DevPulse

### Fast, Free Developer Tools — Right in Your Browser

**30+ essential utilities for developers. No sign-up. No tracking. No nonsense.**

[Live Site](https://devpulse.tools) · [API Docs](https://devpulse.tools/api) · [Report Bug](https://github.com/folger-john/devpulse/issues)

</div>

---

## What is DevPulse?

DevPulse is a collection of 25 developer tools that run instantly in your browser or via a REST API. Every tool is free, fast, and works without creating an account. Built with FastAPI for speed and simplicity.

## Tools

| Category | Tools |
|----------|-------|
| **Data & Encoding** | JSON Formatter, Base64 Encoder/Decoder, URL Encoder/Decoder, HTML Encoder/Decoder, JSON to YAML |
| **Security & Crypto** | Hash Generator (MD5/SHA-1/SHA-256/SHA-512), UUID Generator, Password Generator, JWT Decoder |
| **Text & Content** | Word Counter, Text Case Converter, Lorem Ipsum Generator, Slug Generator, Markdown Preview, Diff Checker |
| **Code & Dev** | Regex Tester, SQL Formatter, CSS Minifier, Cron Expression Parser, HTTP Status Codes |
| **Web & Network** | QR Code Generator, Color Converter, IP Lookup, Chmod Calculator, Unix Timestamp Converter |

## Quick Start

### Run Locally

```bash
git clone https://github.com/folger-john/devpulse.git
cd devpulse
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8090
```

Open [http://localhost:8090](http://localhost:8090) in your browser.

### Self-Hosting (Production)

```bash
# Install dependencies
pip install -r requirements.txt

# Run with uvicorn (production)
uvicorn main:app --host 0.0.0.0 --port 8090 --workers 4

# Or use the included start script
./start.sh
```

For production deployments, put nginx or Caddy in front as a reverse proxy with HTTPS.

## API Usage

All tools are available as REST API endpoints. Free tier: 120 requests/minute.

### Format JSON

```bash
curl -X POST https://devpulse.tools/api/json-format \
  -H "Content-Type: application/json" \
  -d '{"text": "{\"name\": \"devpulse\", \"version\": 1}", "indent": 2}'
```

### Generate Hash

```bash
curl -X POST https://devpulse.tools/api/hash \
  -H "Content-Type: application/json" \
  -d '{"text": "hello world", "algorithm": "sha256"}'
```

### Generate UUID

```bash
curl -X POST https://devpulse.tools/api/uuid \
  -H "Content-Type: application/json" \
  -d '{"version": 4, "count": 3}'
```

### Base64 Encode/Decode

```bash
curl -X POST https://devpulse.tools/api/base64 \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, DevPulse!", "mode": "encode"}'
```

### Generate QR Code

```bash
curl "https://devpulse.tools/api/qr-code?text=https://devpulse.tools" --output qr.png
```

See the full [API documentation](https://devpulse.tools/api) for all endpoints and parameters.

## Tech Stack

- **Backend:** Python 3.11+, [FastAPI](https://fastapi.tiangolo.com/)
- **Server:** Uvicorn (ASGI)
- **Templating:** Jinja2
- **Database:** SQLite (API key storage)
- **QR Codes:** [qrcode](https://pypi.org/project/qrcode/) + Pillow
- **Frontend:** Vanilla HTML/CSS/JS (no framework bloat)

## Screenshots

> Screenshots coming soon. Visit [devpulse.tools](https://devpulse.tools) to see it live.

## Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-new-tool`
3. Make your changes and add tests if applicable
4. Commit: `git commit -m "Add my-new-tool"`
5. Push: `git push origin feature/my-new-tool`
6. Open a Pull Request

### Ideas for contributions

- New developer tools
- UI/UX improvements
- API endpoint enhancements
- Documentation and examples
- Bug fixes

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">

**[devpulse.tools](https://devpulse.tools)** — Built for developers, by developers.

</div>
