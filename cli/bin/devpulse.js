#!/usr/bin/env node
'use strict';

const crypto = require('crypto');
const https = require('https');
const http = require('http');

const VERSION = '1.0.0';
const API_BASE = 'https://devpulse.tools/api';
const FOOTER = '\x1b[2mPowered by DevPulse \u2014 https://devpulse.tools\x1b[0m';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function printFooter() {
  console.error(FOOTER);
}

function die(msg) {
  console.error(`Error: ${msg}`);
  printFooter();
  process.exit(1);
}

function readStdin() {
  return new Promise((resolve, reject) => {
    if (process.stdin.isTTY) return resolve(null);
    const chunks = [];
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (c) => chunks.push(c));
    process.stdin.on('end', () => resolve(chunks.join('')));
    process.stdin.on('error', reject);
  });
}

function readFile(path) {
  return require('fs').readFileSync(path, 'utf8');
}

function apiRequest(path) {
  return new Promise((resolve, reject) => {
    const mod = path.startsWith('https') ? https : http;
    const url = `${API_BASE}${path}`;
    mod.get(url, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        const body = chunks.join('');
        if (res.statusCode >= 400) return reject(new Error(`API ${res.statusCode}: ${body}`));
        try { resolve(JSON.parse(body)); } catch { resolve(body); }
      });
    }).on('error', reject);
  });
}

// ---------------------------------------------------------------------------
// Commands
// ---------------------------------------------------------------------------

async function cmdJson(args, useApi) {
  let input = args[0] ? readFile(args[0]) : await readStdin();
  if (!input) die('No input. Pipe JSON via stdin or pass a file path.');

  if (useApi) {
    // For API mode, POST to the API (simplified: just do local for now since
    // the API endpoint structure may vary)
    console.log('--api mode: falling back to local formatting (no network needed for JSON).');
  }

  try {
    const parsed = JSON.parse(input);
    console.log(JSON.stringify(parsed, null, 2));
  } catch (e) {
    die(`Invalid JSON: ${e.message}`);
  }
  printFooter();
}

function cmdBase64(args, useApi) {
  const sub = args[0];
  const text = args.slice(1).join(' ');
  if (sub === 'encode') {
    if (!text) die('Usage: devpulse base64 encode <text>');
    console.log(Buffer.from(text).toString('base64'));
  } else if (sub === 'decode') {
    if (!text) die('Usage: devpulse base64 decode <text>');
    console.log(Buffer.from(text, 'base64').toString('utf8'));
  } else {
    die('Usage: devpulse base64 encode|decode <text>');
  }
  printFooter();
}

function cmdHash(args) {
  const text = args.join(' ');
  if (!text) die('Usage: devpulse hash <text>');

  const algos = ['md5', 'sha1', 'sha256'];
  for (const algo of algos) {
    const hash = crypto.createHash(algo).update(text).digest('hex');
    console.log(`${algo.toUpperCase().padEnd(6)}  ${hash}`);
  }
  printFooter();
}

function cmdUuid(args) {
  const count = Math.min(parseInt(args[0], 10) || 1, 100);
  for (let i = 0; i < count; i++) {
    console.log(crypto.randomUUID());
  }
  printFooter();
}

function cmdPassword(args) {
  const length = Math.min(Math.max(parseInt(args[0], 10) || 20, 8), 128);
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{}|;:,.<>?';
  const bytes = crypto.randomBytes(length);
  let pw = '';
  for (let i = 0; i < length; i++) {
    pw += chars[bytes[i] % chars.length];
  }
  console.log(pw);
  printFooter();
}

function cmdTimestamp(args) {
  const val = args[0];
  if (!val) {
    // No argument: show current time
    const now = new Date();
    console.log(`Unix (s):   ${Math.floor(now.getTime() / 1000)}`);
    console.log(`Unix (ms):  ${now.getTime()}`);
    console.log(`ISO 8601:   ${now.toISOString()}`);
    console.log(`UTC:        ${now.toUTCString()}`);
    console.log(`Local:      ${now.toString()}`);
  } else {
    // Parse the value
    let date;
    const num = Number(val);
    if (!isNaN(num)) {
      // Detect seconds vs milliseconds
      date = num > 1e12 ? new Date(num) : new Date(num * 1000);
    } else {
      date = new Date(val);
    }
    if (isNaN(date.getTime())) die(`Cannot parse timestamp: ${val}`);

    console.log(`Unix (s):   ${Math.floor(date.getTime() / 1000)}`);
    console.log(`Unix (ms):  ${date.getTime()}`);
    console.log(`ISO 8601:   ${date.toISOString()}`);
    console.log(`UTC:        ${date.toUTCString()}`);
    console.log(`Local:      ${date.toString()}`);
  }
  printFooter();
}

function cmdUrlEncode(args) {
  const text = args.join(' ');
  if (!text) die('Usage: devpulse url-encode <text>');
  console.log(encodeURIComponent(text));
  printFooter();
}

function cmdUrlDecode(args) {
  const text = args.join(' ');
  if (!text) die('Usage: devpulse url-decode <text>');
  try {
    console.log(decodeURIComponent(text));
  } catch (e) {
    die(`Invalid URL-encoded string: ${e.message}`);
  }
  printFooter();
}

function showHelp() {
  console.log(`
devpulse v${VERSION} -- Developer utilities from your terminal

Usage: devpulse <command> [options]

Commands:
  json, json-format          Format JSON from stdin or file
  base64 encode|decode       Base64 encode or decode text
  hash <text>                Show MD5, SHA1, SHA256 hashes
  uuid [count]               Generate UUIDs (default: 1)
  password [length]          Generate a secure password (default: 20 chars)
  timestamp [value]          Convert timestamps (no arg = current time)
  url-encode <text>          URL-encode text
  url-decode <text>          URL-decode text

Options:
  --api                      Use the DevPulse API instead of local processing
  --help, -h                 Show this help
  --version, -v              Show version

Examples:
  echo '{"a":1}' | devpulse json
  devpulse json data.json
  devpulse base64 encode "hello world"
  devpulse hash "my secret"
  devpulse uuid 5
  devpulse password 32
  devpulse timestamp 1700000000
  devpulse url-encode "hello world"
`);
  printFooter();
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const rawArgs = process.argv.slice(2);

  if (rawArgs.includes('--version') || rawArgs.includes('-v')) {
    console.log(`devpulse v${VERSION}`);
    return;
  }

  if (rawArgs.length === 0 || rawArgs.includes('--help') || rawArgs.includes('-h')) {
    showHelp();
    return;
  }

  const useApi = rawArgs.includes('--api');
  const args = rawArgs.filter((a) => a !== '--api');
  const cmd = args[0];
  const cmdArgs = args.slice(1);

  switch (cmd) {
    case 'json':
    case 'json-format':
      await cmdJson(cmdArgs, useApi);
      break;
    case 'base64':
      cmdBase64(cmdArgs, useApi);
      break;
    case 'hash':
      cmdHash(cmdArgs);
      break;
    case 'uuid':
      cmdUuid(cmdArgs);
      break;
    case 'password':
      cmdPassword(cmdArgs);
      break;
    case 'timestamp':
      cmdTimestamp(cmdArgs);
      break;
    case 'url-encode':
      cmdUrlEncode(cmdArgs);
      break;
    case 'url-decode':
      cmdUrlDecode(cmdArgs);
      break;
    default:
      die(`Unknown command: ${cmd}\nRun "devpulse --help" for usage.`);
  }
}

main().catch((e) => die(e.message));
