const BASE = "https://devpulse.tools/tool";

// ── Tool Definitions ──
const TOOLS = [
  { slug: "json-formatter",    name: "JSON Formatter",     icon: "{ }",  desc: "Format & validate JSON" },
  { slug: "base64",            name: "Base64",             icon: "B64",   desc: "Encode / Decode Base64" },
  { slug: "uuid-generator",    name: "UUID Generator",     icon: "ID",    desc: "Generate UUIDs v4" },
  { slug: "hash-generator",    name: "Hash Generator",     icon: "#",     desc: "MD5, SHA-1, SHA-256" },
  { slug: "password-generator",name: "Password Gen",       icon: "***",   desc: "Secure passwords" },
  { slug: "timestamp",         name: "Timestamp",          icon: "\u23F0", desc: "Unix / ISO converter" },
  { slug: "jwt-decoder",       name: "JWT Decoder",        icon: "JWT",   desc: "Decode & inspect JWTs" },
  { slug: "url-encode",        name: "URL Encode",         icon: "%",     desc: "Encode / Decode URLs" },
  { slug: "regex-tester",      name: "Regex Tester",       icon: ".*",    desc: "Test regex patterns" },
  { slug: "color-converter",   name: "Color Converter",    icon: "\uD83C\uDFA8", desc: "HEX, RGB, HSL" },
  { slug: "json-to-yaml",      name: "JSON to YAML",       icon: "Y",     desc: "Convert JSON \u2194 YAML" },
  { slug: "html-encode",       name: "HTML Encode",        icon: "&lt;/&gt;",desc: "Escape HTML entities" },
  { slug: "sql-formatter",     name: "SQL Formatter",      icon: "SQL",   desc: "Format SQL queries" },
  { slug: "css-minifier",      name: "CSS Minifier",       icon: "CSS",   desc: "Minify CSS" },
  { slug: "markdown-preview",  name: "Markdown Preview",   icon: "MD",    desc: "Preview Markdown" },
  { slug: "cron-parser",       name: "Cron Parser",        icon: "\u2691", desc: "Parse cron expressions" },
  { slug: "diff-checker",      name: "Diff Checker",       icon: "\u00B1", desc: "Compare text" },
  { slug: "text-case",         name: "Text Case",          icon: "Aa",    desc: "Change text casing" },
  { slug: "lorem-ipsum",       name: "Lorem Ipsum",        icon: "\u00B6", desc: "Generate placeholder" },
  { slug: "qr-code",           name: "QR Code",            icon: "QR",    desc: "Generate QR codes" },
  { slug: "slug-generator",    name: "Slug Generator",     icon: "/",     desc: "URL-safe slugs" },
  { slug: "word-counter",      name: "Word Counter",       icon: "W#",    desc: "Count words & chars" },
  { slug: "ip-lookup",         name: "IP Lookup",          icon: "IP",    desc: "Lookup IP info" },
  { slug: "http-status",       name: "HTTP Status",        icon: "200",   desc: "HTTP status codes" },
  { slug: "image-to-base64",   name: "Image to Base64",    icon: "IMG",   desc: "Image \u2192 Base64 string" },
  { slug: "json-to-typescript",name: "JSON to TS",         icon: "TS",    desc: "JSON \u2192 TypeScript types" },
  { slug: "yaml-formatter",    name: "YAML Formatter",     icon: "YML",   desc: "Format YAML" },
  { slug: "chmod-calculator",  name: "Chmod Calc",         icon: "755",   desc: "Unix permissions" },
];

// ── Render Tools Grid ──
const grid = document.getElementById("toolsGrid");
for (const tool of TOOLS) {
  const a = document.createElement("a");
  a.className = "tool-card";
  a.href = `${BASE}/${tool.slug}`;
  a.target = "_blank";
  a.dataset.name = tool.name.toLowerCase();
  a.dataset.desc = tool.desc.toLowerCase();
  a.innerHTML = `
    <div class="icon-box">${tool.icon}</div>
    <div class="info">
      <div class="name">${tool.name}</div>
      <div class="desc">${tool.desc}</div>
    </div>`;
  grid.appendChild(a);
}

// ── Search Filter ──
const searchInput = document.getElementById("search");
const noResults = document.getElementById("noResults");

searchInput.addEventListener("input", () => {
  const q = searchInput.value.toLowerCase().trim();
  let visible = 0;
  for (const card of grid.children) {
    const match = !q || card.dataset.name.includes(q) || card.dataset.desc.includes(q);
    card.classList.toggle("hidden", !match);
    if (match) visible++;
  }
  noResults.classList.toggle("visible", visible === 0);
});

// ── Quick Paste / Auto-Detect ──
const pasteArea = document.getElementById("quickPaste");
const detectBar = document.getElementById("detectBar");
const detectType = document.getElementById("detectType");
const detectLink = document.getElementById("detectLink");

const DETECTORS = [
  {
    name: "JSON",
    slug: "json-formatter",
    test: (t) => { try { JSON.parse(t); return t.trim()[0] === "{" || t.trim()[0] === "["; } catch { return false; } },
  },
  {
    name: "JWT",
    slug: "jwt-decoder",
    test: (t) => /^eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(t.trim()),
  },
  {
    name: "Base64",
    slug: "base64",
    test: (t) => /^[A-Za-z0-9+/]{20,}={0,2}$/.test(t.trim()),
  },
  {
    name: "UUID",
    slug: "uuid-generator",
    test: (t) => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(t.trim()),
  },
  {
    name: "Unix Timestamp",
    slug: "timestamp",
    test: (t) => /^\d{10,13}$/.test(t.trim()),
  },
  {
    name: "ISO Date",
    slug: "timestamp",
    test: (t) => /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(t.trim()),
  },
  {
    name: "Color Code",
    slug: "color-converter",
    test: (t) => /^#[0-9a-f]{3,8}$/i.test(t.trim()) || /^rgba?\(/.test(t.trim()) || /^hsla?\(/.test(t.trim()),
  },
  {
    name: "URL",
    slug: "url-encode",
    test: (t) => /^https?:\/\/.+/.test(t.trim()),
  },
  {
    name: "URL-Encoded",
    slug: "url-encode",
    test: (t) => /%[0-9A-Fa-f]{2}/.test(t.trim()) && t.trim().length > 5,
  },
  {
    name: "Cron Expression",
    slug: "cron-parser",
    test: (t) => /^[\d*\/,-]+\s+[\d*\/,-]+\s+[\d*\/,-]+\s+[\d*\/,-]+\s+[\d*\/,-]+/.test(t.trim()),
  },
  {
    name: "Regex",
    slug: "regex-tester",
    test: (t) => /^\/.*\/[gimsuy]*$/.test(t.trim()),
  },
  {
    name: "SQL",
    slug: "sql-formatter",
    test: (t) => /^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\s/i.test(t.trim()),
  },
  {
    name: "Markdown",
    slug: "markdown-preview",
    test: (t) => /^#{1,6}\s/.test(t.trim()) || /^\*\*.+\*\*/.test(t.trim()),
  },
  {
    name: "YAML",
    slug: "yaml-formatter",
    test: (t) => /^---\s*$/.test(t.trim().split("\n")[0]) || (/^\w[\w-]*:\s/.test(t.trim()) && !t.includes("{")),
  },
];

let debounceTimer;
pasteArea.addEventListener("input", () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(detect, 200);
});

function detect() {
  const text = pasteArea.value.trim();
  if (!text) {
    detectBar.classList.remove("visible");
    return;
  }

  for (const d of DETECTORS) {
    if (d.test(text)) {
      detectType.textContent = `Detected: ${d.name}`;
      detectLink.href = `${BASE}/${d.slug}#input=${encodeURIComponent(text)}`;
      detectBar.classList.add("visible");
      return;
    }
  }

  detectBar.classList.remove("visible");
}

// Focus search on popup open
searchInput.focus();
