// Subtitr Grabber — background service worker.
// Listens to all network requests and remembers video-stream URLs per tab
// (HLS .m3u8, DASH .mpd, and direct video files). The popup reads them from
// chrome.storage.session so the list survives the worker sleeping.

const MEDIA_RE = /\.(m3u8|mpd|mp4|m4v|webm|mkv|mov|avi)(\?|#|$)/i;

function classify(url) {
  if (/\.m3u8(\?|#|$)/i.test(url)) return "HLS (m3u8)";
  if (/\.mpd(\?|#|$)/i.test(url)) return "DASH (mpd)";
  return "Video fayl";
}

async function addUrl(tabId, url) {
  if (tabId < 0 || !MEDIA_RE.test(url)) return;
  // Skip HLS fragments (.ts) and tiny key files — we only want manifests / full files.
  if (/\.ts(\?|#|$)/i.test(url)) return;

  const key = "t" + tabId;
  const store = await chrome.storage.session.get(key);
  const list = store[key] || [];
  if (list.some((e) => e.url === url)) return;

  list.unshift({ url, type: classify(url) });
  if (list.length > 40) list.length = 40;
  await chrome.storage.session.set({ [key]: list });

  try {
    await chrome.action.setBadgeText({ tabId, text: String(list.length) });
    await chrome.action.setBadgeBackgroundColor({ tabId, color: "#E6B800" });
  } catch (_) {}
}

chrome.webRequest.onBeforeRequest.addListener(
  (details) => { addUrl(details.tabId, details.url); },
  { urls: ["<all_urls>"] }
);

// Clear a tab's list when it navigates to a new page.
chrome.tabs.onUpdated.addListener((tabId, info) => {
  if (info.status === "loading" && info.url) {
    chrome.storage.session.remove("t" + tabId);
    chrome.action.setBadgeText({ tabId, text: "" }).catch(() => {});
  }
});

chrome.tabs.onRemoved.addListener((tabId) => {
  chrome.storage.session.remove("t" + tabId);
});
