const BASE_URL = "https://devpulse.tools/tool";

// Context menu items
const MENU_ITEMS = [
  { id: "format-json",   title: "Format as JSON",   slug: "json-formatter" },
  { id: "decode-base64", title: "Decode Base64",     slug: "base64" },
  { id: "generate-hash", title: "Generate Hash",     slug: "hash-generator" },
  { id: "url-encode",    title: "URL Encode",        slug: "url-encode" },
  { id: "url-decode",    title: "URL Decode",        slug: "url-encode" },
];

// Create context menus on install
chrome.runtime.onInstalled.addListener(() => {
  // Parent menu
  chrome.contextMenus.create({
    id: "devpulse-parent",
    title: "DevPulse Tools",
    contexts: ["selection"],
  });

  // Child items
  for (const item of MENU_ITEMS) {
    chrome.contextMenus.create({
      id: item.id,
      parentId: "devpulse-parent",
      title: item.title,
      contexts: ["selection"],
    });
  }
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  const menuItem = MENU_ITEMS.find((m) => m.id === info.menuItemId);
  if (!menuItem) return;

  const text = info.selectionText || "";
  const encoded = encodeURIComponent(text);
  const url = `${BASE_URL}/${menuItem.slug}#input=${encoded}`;

  chrome.tabs.create({ url });
});
