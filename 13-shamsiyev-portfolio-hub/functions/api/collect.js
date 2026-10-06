// POST /api/collect — record one page view into D1.
// Never throws to the client; analytics must not break the site.
export async function onRequestPost(context) {
    const { request, env } = context;
    try {
        if (!env.DB) return new Response(null, { status: 204 });

        const ua = request.headers.get("User-Agent") || "";
        // Skip crawlers / bots / previews — we only count real visitors.
        if (/bot|crawl|spider|slurp|bingpreview|facebookexternalhit|embedly|quora link|preview|monitor|uptime|curl|wget|python-requests|headless|lighthouse/i.test(ua)) {
            return new Response(null, { status: 204 });
        }

        let body = {};
        try { body = await request.json(); } catch (_) {}

        const path = String(body.path || new URL(request.url).pathname).slice(0, 300);
        if (path.startsWith("/admin") || path.startsWith("/api")) {
            return new Response(null, { status: 204 }); // don't track the panel itself
        }

        const cf = request.cf || {};
        const ip = request.headers.get("CF-Connecting-IP") || "";
        const ref = String(body.referrer || "").slice(0, 300);
        const { os, browser, device } = parseUA(ua);

        await env.DB.prepare(
            `INSERT INTO visits (ts, path, referrer, country, city, region, ip, ua, device, browser, os, lang, screen, colo)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)`
        ).bind(
            Date.now(),
            path,
            ref,
            cf.country || "",
            cf.city || "",
            cf.region || "",
            ip,
            ua.slice(0, 300),
            device,
            browser,
            os,
            String(body.lang || "").slice(0, 24),
            String(body.screen || "").slice(0, 24),
            cf.colo || ""
        ).run();

        return new Response(null, { status: 204 });
    } catch (_) {
        return new Response(null, { status: 204 });
    }
}

function parseUA(ua) {
    ua = ua || "";
    let os = "Other", browser = "Other", device = "Desktop";
    if (/Android/i.test(ua)) { os = "Android"; device = "Mobile"; }
    else if (/iPhone|iPod/i.test(ua)) { os = "iOS"; device = "Mobile"; }
    else if (/iPad/i.test(ua)) { os = "iOS"; device = "Tablet"; }
    else if (/Windows/i.test(ua)) os = "Windows";
    else if (/Mac OS X|Macintosh/i.test(ua)) os = "macOS";
    else if (/Linux/i.test(ua)) os = "Linux";

    if (/Edg\//i.test(ua)) browser = "Edge";
    else if (/OPR\/|Opera/i.test(ua)) browser = "Opera";
    else if (/SamsungBrowser/i.test(ua)) browser = "Samsung";
    else if (/Chrome\//i.test(ua)) browser = "Chrome";
    else if (/Firefox\//i.test(ua)) browser = "Firefox";
    else if (/Safari\//i.test(ua)) browser = "Safari";

    if (device === "Desktop" && /Mobile/i.test(ua)) device = "Mobile";
    return { os, browser, device };
}
