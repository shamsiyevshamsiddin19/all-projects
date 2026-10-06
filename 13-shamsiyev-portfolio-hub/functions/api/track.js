// Cloudflare Pages Function: /api/track
// Receives the visit beacon from the static site (same-origin, always stable),
// enriches it with the visitor's real IP + country (available at the CF edge),
// and forwards it to the analytics server. If the server's address ever
// changes, update ONE Pages env var (TRACK_UPSTREAM) — the site never changes.
//
// Upstream is a DNS-only (grey-cloud, NOT Cloudflare-proxied) subdomain
// pointing at the Hetzner server's IP. Using the bare IP directly triggers
// Cloudflare error 1003 "Direct IP Access Not Allowed" — because that IP is
// already a protected origin behind another Cloudflare-proxied domain
// (wstore.uz) on this same server, so Cloudflare's edge blocks Workers/Pages
// Functions from fetching it directly. A grey-cloud subdomain sidesteps
// that: Cloudflare only resolves the DNS record and doesn't proxy/protect
// it, so the fetch reaches the server normally. Plain HTTP is fine — this
// runs server-to-server on Cloudflare's edge, not in the visitor's browser,
// so there's no mixed-content/CORS restriction. nginx's default site (any
// Host header) proxies /site/track to subtitr-bot's own admin app, which
// records the visit into PostgreSQL (see web/site_analytics.py).
const DEFAULT_UPSTREAM = "http://track.shamsiyev.uz";

export async function onRequestPost(context) {
    const { request, env } = context;
    const upstream = ((env && env.TRACK_UPSTREAM) || DEFAULT_UPSTREAM).replace(/\/+$/, "");

    let body = "{}";
    try { body = await request.text(); } catch (_) {}

    const cf = request.cf || {};
    const ip = request.headers.get("CF-Connecting-IP") || "";
    const country = cf.country || request.headers.get("CF-IPCountry") || "";
    const city = cf.city || "";
    const region = cf.region || "";
    const org = cf.asOrganization || "";

    // Forward in the background so the visitor's request returns instantly.
    context.waitUntil((async () => {
        try {
            await fetch(upstream + "/site/track", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "User-Agent": request.headers.get("User-Agent") || "",
                    "X-Visitor-Ip": ip,
                    "X-Visitor-Country": country,
                    "X-Visitor-City": city,
                    "X-Visitor-Region": region,
                    "X-Visitor-Org": org,
                    "Origin": "https://shamsiyev.uz",
                },
                body,
            });
        } catch (_) {}
    })());

    return new Response(null, { status: 204 });
}

export function onRequestOptions() {
    return new Response(null, { status: 204 });
}
