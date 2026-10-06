// Lightweight, cookie-free visit beacon. Sends one ping per page load to
// /api/track (a Cloudflare Pages Function that forwards to the analytics
// server). An anonymous visitor id is kept in localStorage to count uniques.
(function () {
    try {
        var KEY = "sh_vid";
        var vid = localStorage.getItem(KEY);
        if (!vid) {
            vid = Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
            localStorage.setItem(KEY, vid);
        }
        var payload = JSON.stringify({
            v: vid,
            p: location.pathname + location.search,
            r: document.referrer || "",
            l: navigator.language || "",
            s: (screen.width || 0) + "x" + (screen.height || 0),
            tz: (Intl.DateTimeFormat().resolvedOptions().timeZone) || ""
        });
        if (navigator.sendBeacon) {
            navigator.sendBeacon("/api/track", new Blob([payload], { type: "application/json" }));
        } else {
            fetch("/api/track", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: payload,
                keepalive: true
            });
        }
    } catch (e) { /* analytics must never break the page */ }
})();
