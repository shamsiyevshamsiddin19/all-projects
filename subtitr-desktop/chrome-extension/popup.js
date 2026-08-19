async function currentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

function shorten(url) {
  return url.length > 90 ? url.slice(0, 60) + " … " + url.slice(-25) : url;
}

async function copy(text, msgEl) {
  try {
    await navigator.clipboard.writeText(text);
  } catch (_) {
    // Fallback for restricted contexts.
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  }
  if (msgEl) {
    msgEl.style.display = "inline";
    setTimeout(() => { msgEl.style.display = "none"; }, 1500);
  }
}

async function render() {
  const tab = await currentTab();
  const key = "t" + tab.id;
  const store = await chrome.storage.session.get(key);
  const items = store[key] || [];
  const list = document.getElementById("list");
  list.innerHTML = "";

  if (items.length === 0) {
    list.innerHTML =
      '<div class="empty">Bu sahifada video oqim topilmadi.<br>' +
      'Videoni <b>o\'ynating</b> (Play bosing), keyin bu oynani qayta oching.</div>';
  } else {
    for (const it of items) {
      const div = document.createElement("div");
      div.className = "item";

      const type = document.createElement("div");
      type.className = "type";
      type.textContent = it.type;

      const url = document.createElement("div");
      url.className = "url";
      url.textContent = shorten(it.url);

      const btn = document.createElement("button");
      btn.textContent = "Nusxa olish";
      const msg = document.createElement("span");
      msg.className = "copied";
      msg.style.display = "none";
      msg.textContent = "Nusxalandi ✓";
      btn.addEventListener("click", () => copy(it.url, msg));

      div.appendChild(type);
      div.appendChild(url);
      div.appendChild(btn);
      div.appendChild(msg);
      list.appendChild(div);
    }
  }

  const copyPage = document.getElementById("copyPage");
  const pageMsg = document.getElementById("pageMsg");
  copyPage.addEventListener("click", () => copy(tab.url, pageMsg));
}

render();
