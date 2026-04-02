# devpulse-cli

Developer utilities from your terminal. JSON formatting, base64, hashing, UUIDs, password generation, timestamp conversion, and URL encoding -- all offline, zero dependencies.

## Install

```bash
npm install -g devpulse-cli
```

Or use directly with npx:

```bash
npx devpulse-cli json-format < data.json
```

## Commands

| Command | Description |
|---|---|
| `devpulse json [file]` | Format JSON from stdin or file |
| `devpulse base64 encode\|decode <text>` | Base64 encode or decode |
| `devpulse hash <text>` | Show MD5, SHA1, SHA256 hashes |
| `devpulse uuid [count]` | Generate UUIDs |
| `devpulse password [length]` | Generate a secure password |
| `devpulse timestamp [value]` | Convert timestamps |
| `devpulse url-encode <text>` | URL-encode text |
| `devpulse url-decode <text>` | URL-decode text |

## Examples

```bash
# Format JSON
echo '{"name":"DevPulse","version":1}' | devpulse json

# Base64
devpulse base64 encode "hello world"
devpulse base64 decode "aGVsbG8gd29ybGQ="

# Hashing
devpulse hash "my secret string"

# UUIDs
devpulse uuid 5

# Passwords
devpulse password 32

# Timestamps
devpulse timestamp              # current time
devpulse timestamp 1700000000   # from unix seconds
devpulse timestamp 2025-01-01   # from date string

# URL encoding
devpulse url-encode "hello world & more"
devpulse url-decode "hello%20world%20%26%20more"
```

## API Mode

Add `--api` to any command to use the DevPulse web API instead of local processing:

```bash
devpulse json --api < data.json
```

## License

MIT
